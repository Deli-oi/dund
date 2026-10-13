"""Label confidence c = decisiveness x evidence quality (docs/16)."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

FACTORS = (
    "entity_resolution",
    "outcome_measurement",
    "horizon_completeness",
    "voter_agreement",
    "confounder_risk",
    "timing_clarity",
)


def decisiveness(p: float) -> float:
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0, 1]")
    return abs(2.0 * p - 1.0)


def evidence_quality(factors: dict[str, float]) -> float:
    q = 1.0
    for name in FACTORS:
        v = factors.get(name, 1.0)
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"factor {name} must be in [0, 1]")
        q *= v
    return q


def confidence(p: float, factors: dict[str, float]) -> float:
    return decisiveness(p) * evidence_quality(factors)


def reasons(factors: dict[str, float], below: float = 0.8) -> list[str]:
    return [n for n in FACTORS if factors.get(n, 1.0) < below]


def example_weight(c: float, age_years: float, half_life_years: float,
                   materiality: float = 1.0, cluster_k: int = 1) -> float:
    """w = c x decay x materiality x 1/sqrt(k) (docs/17). Per-ticker cap applied elsewhere."""
    decay = 0.5 ** (age_years / half_life_years)
    return c * decay * max(materiality, 0.2) / math.sqrt(max(cluster_k, 1))


def effective_n(weights: list[float]) -> float:
    s = sum(weights)
    s2 = sum(w * w for w in weights)
    return (s * s / s2) if s2 > 0 else 0.0


@dataclass
class LabelRow:
    post_id: str
    p: float
    factors: dict[str, float] = field(default_factory=dict)

    @property
    def c(self) -> float:
        return confidence(self.p, self.factors)
