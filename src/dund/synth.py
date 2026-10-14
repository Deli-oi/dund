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

# ---------------------------------------------------------------------------
# v2: generator for the REAL estimand (docs/38 D1, D4, D8)
#   net abnormal 10-day return of flagged ticker-days minus matched-control mean,
#   one-sided two-way (ticker, calendar week) clustered bootstrap lower bound > 0.
# Simulated at the flagged-unit level: each flagged unit gets `n_ctrl` matched
# controls (same ticker, non-flagged, other week). Ticker-days N = n_flag / flag_rate
# fixes the calendar span (N_PER_WEEK ticker-days a week) and the ticker universe.
# ---------------------------------------------------------------------------
import bisect

N_PER_WEEK = 400        # ticker-days a week (about 20k a year, inside docs/28 range)
COST_BPS = 20           # round-trip cost; gross edge = net edge + cost (edge is planted NET)


@dataclass
class V2Data:
    d: list        # flagged net abnormal return minus mean of its matched controls
    ticker: list   # ticker index per flagged unit
    week: list     # calendar week per flagged unit
    n_days: int    # implied ticker-days N
    n_weeks: int


def generate_v2(n_flag=200, flag_rate=0.005, edge_bps=0.0, seed=0, n_ctrl=3,
                sd_idio=0.06, sd_ticker=0.02, sd_week=0.03, meme_week_frac=0.06,
                meme_flag_share=0.6, meme_vol_mult=2.0, p_hi_flag=0.35, p_hi_ctrl=0.15,
                hi_mult=2.2, regime_break=False) -> V2Data:
    """Total 10-day sd is about 9 to 10%. Components: ticker random effect, a
    calendar-week common shock (larger in meme weeks), idiosyncratic noise from
    ticker-week innovations (a 10-day window spans 3 calendar weeks, so windows
    overlap and neighbours share innovations), heavier tails on high-attention days.
    regime_break: planted edge exists only in the first half of the calendar."""
    rng = random.Random(seed)
    gauss, rnd = rng.gauss, rng.random
    N = max(1, round(n_flag / flag_rate))
    W = max(8, round(N / N_PER_WEEK))
    T = max(50, min(1500, N // 10))
    n_meme = max(2, round(meme_week_frac * W))
    memes = rng.sample(range(W), min(n_meme, W))
    meme_set = set(memes)
    cum, s = [], 0.0
    for k in range(T):          # Zipf-like ticker activity: a few tickers repeat
        s += 1.0 / (k + 1) ** 0.7
        cum.append(s)
    u = [gauss(0, sd_ticker) for _ in range(T)]
    m, idio = {}, {}

    def week_comp(w):
        v = m.get(w)
        if v is None:
            v = m[w] = gauss(0, sd_week * (meme_vol_mult if w in meme_set else 1.0))
        return v

    def window(tk, w, dow, hi_p):
        f1, f3 = (5 - dow) / 5.0, dow / 5.0
        tot = 0.0
        for wk, f in ((w, f1), (w + 1, 1.0), (w + 2, f3)):
            if f == 0.0:
                continue
            key = (tk, wk)
            z = idio.get(key)
            if z is None:
                z = idio[key] = gauss(0, 1.0)
            tot += f * (sd_idio * z + week_comp(wk))
        r = tot / math.sqrt(f1 * f1 + 1.0 + f3 * f3)
        if rnd() < hi_p:        # volatility clustering: fat shock on high-attention days
            r += (hi_mult - 1.0) * sd_idio * gauss(0, 1.0)
        return r + u[tk]

    edge = edge_bps / 1e4
    d, tks, wks = [], [], []
    for _ in range(n_flag):
        if rnd() < meme_flag_share:
            w = memes[int(rnd() * len(memes))]
        else:
            w = int(rnd() * W)
        tk = min(T - 1, bisect.bisect_left(cum, rnd() * s))
        r = window(tk, w, int(rnd() * 5), p_hi_flag)
        if edge and not (regime_break and w >= W // 2):
            r += edge
        c = 0.0
        for _ in range(n_ctrl):
            c += window(tk, int(rnd() * W), int(rnd() * 5), p_hi_ctrl)
        d.append(r - c / n_ctrl); tks.append(tk); wks.append(w)
    return V2Data(d, tks, wks, N, W)


def boot_lower_bounds(data: V2Data, B=199, rng=None, alpha=0.05) -> dict:
    """One-sided lower bounds (alpha quantile of the bootstrap) of the mean
    difference under three clusterings: 'ticker' (negative control, not
    accepted by D4), 'week', and 'two_way' (product of independent Exp(1)
    ticker and week weights, a multiplier bootstrap)."""
    rng = rng or random.Random(0)
    n = len(data.d)
    if n == 0:
        return {"ticker": -1.0, "week": -1.0, "two_way": -1.0, "mean": 0.0}
    tmap, wmap = {}, {}
    ti = [tmap.setdefault(t, len(tmap)) for t in data.ticker]
    wi = [wmap.setdefault(w, len(wmap)) for w in data.week]
    d = data.d
    nt, nw = len(tmap), len(wmap)
    ex = rng.expovariate
    out = {"ticker": [], "week": [], "two_way": []}
    for _ in range(B):
        a = [ex(1.0) for _ in range(nt)]
        b = [ex(1.0) for _ in range(nw)]
        sa = sb = sab = na = nb = nab = 0.0
        for i in range(n):
            x = a[ti[i]]; y = b[wi[i]]; v = d[i]
            sa += x * v; na += x
            sb += y * v; nb += y
            xy = x * y
            sab += xy * v; nab += xy
        out["ticker"].append(sa / na); out["week"].append(sb / nb); out["two_way"].append(sab / nab)
    k = max(0, int(alpha * B) - 1)
    res = {name: sorted(v)[k] for name, v in out.items()}
    res["mean"] = sum(d) / n
    return res
