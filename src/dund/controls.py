"""Matched same-ticker controls (D4), clustered-bootstrap estimator, balance.

Time is a per-ticker trading-day index.  The decision time of a candidate day
t is the open of day t: features use only indices < t.  The outcome window is
[t, t+window) of the abnormal-return series `ar`.
"""
import math
import random
from dataclasses import dataclass, field

FEATURES = ("r5", "r21", "volratio", "vol21", "mentions")
MIN_HISTORY = 31


@dataclass
class Series:
    ticker: str
    ret: list          # daily return
    vol: list          # daily volume
    mentions: list     # daily mention count
    ar: list           # daily abnormal return (outcome)
    week: list         # calendar week label per day
    flagged: set = field(default_factory=set)   # flagged day indices
    posted: set = field(default_factory=set)    # other posted day indices


def features(s: Series, t: int):
    """Feature vector from data strictly before day t, or None."""
    if t < MIN_HISTORY:
        return None
    r = s.ret
    r5 = sum(r[t - 5:t])
    r21 = sum(r[t - 21:t])
    base = sum(s.vol[t - 30:t]) / 30.0
    vr = s.vol[t - 1] / base if base > 0 else 1.0
    w = r[t - 21:t]
    m = sum(w) / 21.0
    sd = math.sqrt(sum((x - m) ** 2 for x in w) / 20.0)
    men = sum(s.mentions[t - 5:t])
    return [r5, r21, vr, sd, float(men)]


def outcome(s: Series, t: int, window: int):
    if t + window > len(s.ar):
        return None
    return sum(s.ar[t:t + window])


def _sds(rows):
    out = []
    for j in range(len(rows[0])):
        c = [r[j] for r in rows]
        m = sum(c) / len(c)
        v = sum((x - m) ** 2 for x in c) / max(len(c) - 1, 1)
        out.append(math.sqrt(v) or 1.0)
    return out


def match_controls(s: Series, window=10, lookaround=40, exclusion=10,
                   caliper=1.0, targets=None):
    """Return (pairs, unmatched).  pairs: dicts with ticker, week, flagged_t,
    control_t, diff (flagged minus control outcome), distance.  Caliper is the
    maximum per-feature absolute difference in pooled SD units."""
    targets = sorted(s.flagged if targets is None else targets)
    events = set(s.flagged) | set(s.posted)
    n = len(s.ret)
    cand_all = []
    for c in range(MIN_HISTORY, n - window + 1):
        if any(abs(c - e) <= exclusion for e in events):
            continue
        f = features(s, c)
        if f is not None:
            cand_all.append((c, f))
    tf = {t: features(s, t) for t in targets}
    pool = [f for _, f in cand_all] + [f for f in tf.values() if f]
    sds = _sds(pool) if pool else []
    used = []
    pairs, unmatched = [], []
    for t in targets:
        f = tf[t]
        y = outcome(s, t, window)
        if f is None or y is None:
            unmatched.append({"ticker": s.ticker, "t": t, "reason": "no_history_or_outcome"})
            continue
        near = [(c, g) for c, g in cand_all if abs(c - t) <= lookaround]
        near = [(c, g) for c, g in near if all(abs(c - u) >= window for u in used)]
        if not near:
            unmatched.append({"ticker": s.ticker, "t": t, "reason": "no_candidates"})
            continue
        best = None
        for c, g in near:
            z = [abs(a - b) / sd for a, b, sd in zip(f, g, sds)]
            if max(z) > caliper:
                continue
            d = math.sqrt(sum(x * x for x in z))
            if best is None or d < best[0]:
                best = (d, c)
        if best is None:
            unmatched.append({"ticker": s.ticker, "t": t, "reason": "caliper"})
            continue
        c = best[1]
        used.append(c)
        pairs.append({"ticker": s.ticker, "week": s.week[t], "flagged_t": t,
                      "control_t": c, "diff": y - outcome(s, c, window),
                      "distance": best[0]})
    return pairs, unmatched


def match_all(series, **kw):
    pairs, un = [], []
    for s in series:
        p, u = match_controls(s, **kw)
        pairs += p
        un += u
    reasons = {}
    for u in un:
        reasons[u["reason"]] = reasons.get(u["reason"], 0) + 1
    return {"pairs": pairs, "unmatched": un, "n_unmatched": len(un), "reasons": reasons}


def boot_estimate(pairs, cluster="two_way", B=999, alpha=0.05, rng=None):
    """Mean diff with one-sided lower bound.  cluster: 'two_way' (multiplier
    bootstrap, independent Exp(1) weights on tickers and weeks) or 'ticker'
    (negative control only, not accepted by D4)."""
    rng = rng or random.Random(0)
    if not pairs:
        return {"mean": 0.0, "lower": float("-inf"), "p": 1.0, "n": 0}
    cells = {}
    for p in pairs:
        a = cells.setdefault((p["ticker"], p["week"]), [0.0, 0])
        a[0] += p["diff"]
        a[1] += 1
    tk = {t: i for i, t in enumerate(sorted({k[0] for k in cells}, key=str))}
    wk = {w: i for i, w in enumerate(sorted({k[1] for k in cells}, key=str))}
    items = [(tk[t], wk[w], s, c) for (t, w), (s, c) in cells.items()]
    mean = sum(i[2] for i in items) / sum(i[3] for i in items)
    means = []
    for _ in range(B):
        a = [rng.expovariate(1.0) for _ in tk]
        b = [rng.expovariate(1.0) for _ in wk] if cluster == "two_way" else None
        num = den = 0.0
        for ti, wi, s, c in items:
            x = a[ti] * (b[wi] if b else 1.0)
            num += x * s
            den += x * c
        means.append(num / den if den else 0.0)
    means.sort()
    lower = means[max(int(alpha * B) - 1, 0)]
    p = (1 + sum(1 for m in means if m <= 0)) / (B + 1)
    return {"mean": mean, "lower": lower, "p": p, "n": len(pairs)}


def holm(pvals, alpha=0.05):
    """Holm step-down.  Returns (adjusted p list, reject list) in input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * pvals[i]))
        adj[i] = run
    return adj, [a <= alpha for a in adj]


def _smd(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    sd = math.sqrt((va + vb) / 2) or 1.0
    return (ma - mb) / sd


def balance_report(series, pairs, window=10, exclusion=10):
    """Standardized mean differences (flagged minus comparison).  'before'
    compares flagged days with all eligible same-ticker days; 'after'
    compares the matched pairs."""
    by = {s.ticker: s for s in series}
    fl, ct, allc = [], [], []
    for p in pairs:
        s = by[p["ticker"]]
        fl.append(features(s, p["flagged_t"]))
        ct.append(features(s, p["control_t"]))
    for s in series:
        ev = set(s.flagged) | set(s.posted)
        for c in range(MIN_HISTORY, len(s.ret) - window + 1):
            if all(abs(c - e) > exclusion for e in ev):
                allc.append(features(s, c))
    out = {}
    for j, name in enumerate(FEATURES):
        col = lambda rows: [r[j] for r in rows]
        out[name] = {"before": _smd(col(fl), col(allc)),
                     "after": _smd(col(fl), col(ct))}
    return out
