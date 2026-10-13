"""Spend and request ledger with hard caps and a KILL file (docs/11 rules 4 and 7)."""
from __future__ import annotations

import json
import time
from pathlib import Path


class CapExceeded(RuntimeError):
    pass


class Killed(RuntimeError):
    pass


class Ledger:
    def __init__(self, path: Path, caps: dict[str, float], kill_file: Path | None = None):
        self.path = Path(path)
        self.caps = dict(caps)
        self.kill_file = Path(kill_file) if kill_file else self.path.with_name("KILL")

    def totals(self) -> dict[str, float]:
        out: dict[str, float] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    out[row["kind"]] = out.get(row["kind"], 0.0) + float(row["amount"])
        return out

    def check(self, kind: str, amount: float = 0.0) -> None:
        if self.kill_file.exists():
            raise Killed(f"kill file present: {self.kill_file}")
        cap = self.caps.get(kind)
        if cap is not None and self.totals().get(kind, 0.0) + amount > cap:
            raise CapExceeded(f"{kind}: {amount} would exceed cap {cap}")

    def record(self, kind: str, amount: float, note: str = "") -> None:
        self.check(kind, amount)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": time.time(), "kind": kind, "amount": amount, "note": note}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
