"""Action report rows: margin over the decision threshold (docs/18)."""
from __future__ import annotations

from dataclasses import dataclass


def breakeven_threshold(gain: float, loss: float, safety: float = 0.20) -> float:
    """p* = loss / (loss + gain) + safety margin, capped at 1 (docs/04, docs/07)."""
    return min(1.0, loss / (loss + gain) + safety)


@dataclass
class Call:
    asset: str
    post_id: str
    p: float
    p_lower: float
    p_upper: float
    threshold: float
    se: float = 0.0
    confounded: bool = False
    illiquid: bool = False

    @property
    def margin(self) -> float:
        return self.p_lower - self.threshold

    @property
    def margin_z(self) -> float:
        return (self.p - self.threshold) / self.se if self.se > 0 else float("nan")

    @property
    def action(self) -> str:
        if self.confounded or self.illiquid:
            return "SKIP"
        if self.margin > 0:
            return "ACT"
        if self.p > self.threshold:
            return "WATCH"
        return "SKIP"


def rank(calls: list[Call]) -> list[Call]:
    """Rank by margin, not by point probability."""
    return sorted(calls, key=lambda c: c.margin, reverse=True)
