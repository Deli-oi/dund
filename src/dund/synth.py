"""Synthetic ticker-day datasets with a planted effect (pure stdlib)."""
from __future__ import annotations
import math, random
from dataclasses import dataclass


@dataclass
class SynthData:
    ticker: list   # cluster id per ticker-day
    day: list      # day index per ticker-day
    flag: list     # 0/1
    hit: list      # 0/1


def generate(n_ticker_days=5000, base_rate=0.05, flagged_rate=None, flag_rate=0.02,
             days_per_ticker=4.0, cluster_sd=0.5, n_days=250, regime_shift_day=None,
             seed=0) -> SynthData:
    """flagged_rate: hit prob for flagged items (None => null, equals base_rate).
    cluster_sd: sd of log-normal ticker multiplier (mean 1) -> within-ticker correlation.
    regime_shift_day: flagged effect vanishes for day >= this index."""
    rng = random.Random(seed)
    if flagged_rate is None:
        flagged_rate = base_rate
    n_t = max(1, round(n_ticker_days / days_per_ticker))
    mult = [math.exp(rng.gauss(0, cluster_sd) - cluster_sd ** 2 / 2) for _ in range(n_t)]
    t, d, f, h = [], [], [], []
    for i in range(n_ticker_days):
        k = rng.randrange(n_t)
        day = rng.randrange(n_days)
        fl = 1 if rng.random() < flag_rate else 0
        p = base_rate
        if fl and not (regime_shift_day is not None and day >= regime_shift_day):
            p = flagged_rate
        p = min(0.95, p * mult[k])
        t.append(k); d.append(day); f.append(fl); h.append(1 if rng.random() < p else 0)
    return SynthData(t, d, f, h)


def cluster_permutation_pvalue(data: SynthData, n_perm=199, rng=None) -> float:
    """One-sided test that the flagged hit rate exceeds the unflagged rate.
    Flags are permuted WITHIN ticker (respects clustering); with fixed flag
    count the statistic is monotone in flagged hits, so we count those.
    Returns add-one p-value."""
    rng = rng or random.Random(0)
    by = {}
    for k, fl, hit in zip(data.ticker, data.flag, data.hit):
        c = by.setdefault(k, [0, 0, 0, 0])  # size, hits, flags, flagged hits
        c[0] += 1; c[1] += hit; c[2] += fl; c[3] += fl * hit
    cl = [c for c in by.values() if c[2] > 0 and 0 < c[1] < c[0]]  # informative
    if not cl:
        return 1.0
    obs = sum(c[3] for c in cl)
    rnd = rng.random
    ge = 0
    for _ in range(n_perm):
        s = 0
        for size, hits, nf, _fh in cl:
            if nf == 1:
                s += rnd() * size < hits
            else:
                s += sum(rng.sample([1] * hits + [0] * (size - hits), nf))
        ge += s >= obs
    return (ge + 1) / (n_perm + 1)
