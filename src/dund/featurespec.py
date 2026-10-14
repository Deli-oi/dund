"""Frozen feature spec: the contract between training vectors and live vectors.

Model-agnostic, stdlib only. A spec fixes column order, dtype, encoding and the
missing-value rule per column, plus the versions of everything upstream
(transform, resolver / ticker table, decision-time rule). Its sha256 hash is
stored with the model; the scorer refuses to run on a mismatch (doc 38 D12).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Tuple

DTYPES = ("int", "float", "str", "bool")
MISSING_RULES = ("error", "marker")  # error: None refused. marker: emit column.marker


class SpecError(ValueError):
    pass


class SpecHashMismatch(SpecError):
    pass


class ParityError(AssertionError):
    pass


@dataclass(frozen=True)
class Column:
    name: str
    dtype: str                      # one of DTYPES
    encoding: str = "raw"           # free-text rule, hashed (e.g. "log1p")
    missing: str = "error"          # one of MISSING_RULES
    marker: Any = None              # emitted when missing == "marker" and value is None

    def __post_init__(self):
        if self.dtype not in DTYPES:
            raise SpecError(f"column {self.name}: unknown dtype {self.dtype!r}")
        if self.missing not in MISSING_RULES:
            raise SpecError(f"column {self.name}: unknown missing rule {self.missing!r}")

    def to_dict(self) -> dict:
        return {"name": self.name, "dtype": self.dtype, "encoding": self.encoding,
                "missing": self.missing, "marker": self.marker}


def _coerce(col: Column, v: Any) -> Any:
    t = col.dtype
    if t == "bool":
        if isinstance(v, bool):
            return v
        raise SpecError(f"column {col.name}: expected bool, got {type(v).__name__}")
    if t == "int":
        if isinstance(v, bool) or not isinstance(v, int):
            raise SpecError(f"column {col.name}: expected int, got {type(v).__name__}")
        return v
    if t == "float":
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise SpecError(f"column {col.name}: expected float, got {type(v).__name__}")
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            raise SpecError(f"column {col.name}: non-finite float (use None plus marker rule)")
        return f
    if not isinstance(v, str):
        raise SpecError(f"column {col.name}: expected str, got {type(v).__name__}")
    return v


@dataclass(frozen=True)
class FeatureSpec:
    columns: Tuple[Column, ...]
    transform_version: str
    resolver_version: str           # resolver + point-in-time ticker table version or hash
    decision_rule: str = "00:00 UTC next day; posts with created_at <= decision time (doc 38 D2)"
    window_rule: str = "trailing 30d and 90d prior post counts, finalized days only"
    extra: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise SpecError("duplicate column names")
        object.__setattr__(self, "columns", tuple(self.columns))

    @property
    def names(self) -> List[str]:
        return [c.name for c in self.columns]

    def to_dict(self) -> dict:
        return {"columns": [c.to_dict() for c in self.columns],
                "transform_version": self.transform_version,
                "resolver_version": self.resolver_version,
                "decision_rule": self.decision_rule,
                "window_rule": self.window_rule,
                "extra": dict(sorted(self.extra.items()))}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @classmethod
    def from_json(cls, s: str) -> "FeatureSpec":
        d = json.loads(s)
        return cls(columns=tuple(Column(**c) for c in d["columns"]),
                   transform_version=d["transform_version"],
                   resolver_version=d["resolver_version"],
                   decision_rule=d["decision_rule"], window_rule=d["window_rule"],
                   extra=d.get("extra", {}))

    @property
    def spec_hash(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def check(self, spec_hash: str) -> None:
        if spec_hash != self.spec_hash:
            raise SpecHashMismatch(
                f"spec hash mismatch: bundle {spec_hash[:12]}, scorer {self.spec_hash[:12]}")

    def vectorize(self, row: Dict[str, Any]) -> list:
        names = self.names
        unknown = [k for k in row if k not in names]
        if unknown:
            raise SpecError(f"unknown columns: {sorted(unknown)}")
        absent = [n for n in names if n not in row]
        if absent:
            raise SpecError(f"missing columns: {absent}")
        out = []
        for c in self.columns:
            v = row[c.name]
            if v is None:
                if c.missing != "marker":
                    raise SpecError(f"column {c.name}: missing value not allowed")
                out.append(c.marker)
            else:
                out.append(_coerce(c, v))
        return out


def assert_parity(census_rows: Iterable[dict], live_rows: Iterable[dict],
                  spec: FeatureSpec) -> int:
    """Vectorize two row streams built from the same raw posts by different paths.

    Rows are compared pairwise in order. Raises ParityError naming the first
    differing row index and column. Returns the number of rows compared.
    """
    a, b = list(census_rows), list(live_rows)
    if len(a) != len(b):
        raise ParityError(f"row count differs: census {len(a)} vs live {len(b)}")
    names = spec.names
    for i, (ra, rb) in enumerate(zip(a, b)):
        va, vb = spec.vectorize(ra), spec.vectorize(rb)
        for n, x, y in zip(names, va, vb):
            if x != y:
                raise ParityError(f"row {i}, column {n!r}: census {x!r} != live {y!r}")
    return len(a)
