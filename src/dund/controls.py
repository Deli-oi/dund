"""Matched same-ticker controls (D4), clustered-bootstrap estimator, balance (docs/43).

Timing and outcome come from labels.py: a ticker-day with UTC date d has
decision_ts = 00:00 UTC of d+1 and enters at labels.entry_index (first close
strictly after).  Every matching feature uses only price rows with index
< entry index (closes at or before decision time) and posts dated before d.
The outcome for flagged and control days is labels.label_event's CAR over the
window (entry close to close `window` days later, benchmark-adjusted) minus the
round-trip cost.  Sealed periods (sealed.py) never supply a control.
"""
import csv
import gzip
import math
import os
import random
from bisect import bisect_left, bisect_right
from statistics import NormalDist
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from dund import labels
from dund.sealed import UNSEAL_TOKEN, is_sealed_event

FEATURES = ("r5", "r21", "volratio", "vol21", "mentions")
MIN_HISTORY = 31
COST = 0.0020
LOOKBACK_CAL_DAYS = 45   # feature history reaches back at most ~31 trading days


@dataclass
class Cand:
    idx: int            # entry index in the ticker's price series
    day: date           # UTC date of the ticker-day
    week: tuple         # ISO (year, week) of the ticker-day
    feat: list          # FEATURES vector or None
    net: dict           # window -> net abnormal return or None


@dataclass
class Table:
    ticker: str
    cands: list                                   # eligible control candidates
    flagged: list                                 # flagged Cand, any sealed/feature status
    posted_idx: list = field(default_factory=list)    # sorted entry idx of ALL posted days
    sealed_flagged: list = field(default_factory=list)  # flagged days skipped as sealed


def decision_ts(d: date) -> datetime:
    """00:00 UTC of the next day (D2)."""
    n = d + timedelta(days=1)
    return datetime(n.year, n.month, n.day, tzinfo=timezone.utc)


def _std(x):
    m = sum(x) / len(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


def features_at(ps, i0, d, posted_dates):
    """Feature vector from price rows with index < i0 and posts dated < d."""
    if i0 < MIN_HISTORY:
        return None
    a, v = ps.adj_close, ps.volume
    r5 = a[i0 - 1] / a[i0 - 6] - 1.0
    r21 = a[i0 - 1] / a[i0 - 22] - 1.0
    base = sum(v[i0 - 31:i0 - 1]) / 30.0
    vr = v[i0 - 1] / base if base > 0 else 1.0
    rets = [a[j] / a[j - 1] - 1.0 for j in range(i0 - 21, i0)]
    men = sum(1 for k in range(1, 8) if (d - timedelta(days=k)) in posted_dates)
    return [r5, r21, vr, _std(rets), float(men)]


def net_outcomes(ticker, d, ps, bench, windows, cost=COST):
    """Net CAR per window, produced by labels.label_event (no re-implementation)."""
    lab = labels.label_event(ticker, decision_ts(d), ps, bench, windows=tuple(windows),
                             min_placebo=1, lookback=0)
    out = {}
    for w in windows:
        win = lab.windows.get(w)
        out[w] = None if win is None or win.car is None else win.car - cost
    return out, lab


def _is_sealed(d, maxw):
    ts = decision_ts(d)
    return (is_sealed_event(ts, maxw)
            or is_sealed_event(d - timedelta(days=LOOKBACK_CAL_DAYS), maxw + 32))


def build_table(ticker, ps, bench, posted_dates, flagged_dates, windows=(5, 10, 21),
                cost=COST, unseal_token=None, exclusion=10):
    """Candidates exclude: sealed days (unless the unseal token is given), days
    within +/-max(exclusion, max window - 1) entry days of any posted ticker-day."""
    posted_dates, flagged_dates = set(posted_dates), set(flagged_dates)
    maxw = max(windows)
    unsealed = unseal_token == UNSEAL_TOKEN
    ep = {}
    for d in posted_dates | flagged_dates:
        i = labels.entry_index(ps, decision_ts(d))
        if i is not None:
            ep[d] = i
    posted_idx = sorted(ep.values())
    margin = max(exclusion, maxw - 1)

    def make(d, i0):
        f = features_at(ps, i0, d, posted_dates)
        net, _ = net_outcomes(ticker, d, ps, bench, windows, cost) if f is not None \
            else ({w: None for w in windows}, None)
        return Cand(i0, d, tuple(d.isocalendar())[:2], f, net)

    fl, sealed_fl = [], []
    for d in sorted(flagged_dates):
        if d not in ep:
            continue
        if not unsealed and _is_sealed(d, maxw):
            sealed_fl.append(d)
            continue
        fl.append(make(d, ep[d]))
    cands = []
    for k in range(len(ps)):
        d = ps.dates[k]
        i0 = labels.entry_index(ps, decision_ts(d))
        if i0 is None or i0 < MIN_HISTORY:
            continue
        j = bisect_left(posted_idx, i0 - margin)
        if j < len(posted_idx) and posted_idx[j] <= i0 + margin:
            continue                      # a control must not itself be an event
        if not unsealed and _is_sealed(d, maxw):
            continue
        c = make(d, i0)
        if c.feat is not None:
            cands.append(c)
    return Table(ticker, cands, fl, posted_idx, sealed_fl)


def _sds(rows):
    out = []
    for j in range(len(rows[0])):
        c = [r[j] for r in rows]
        m = sum(c) / len(c)
        v = sum((x - m) ** 2 for x in c) / max(len(c) - 1, 1)
        out.append(math.sqrt(v) or 1.0)
    return out


def match_controls(tab, window=10, lookaround=40, caliper=1.0):
    """Return (pairs, unmatched).  Greedy in time order, no replacement,
    non-overlapping control windows, caliper on every feature in pooled SD."""
    cands = [c for c in tab.cands if c.net.get(window) is not None]
    targets = sorted(tab.flagged, key=lambda c: c.idx)
    pool = [c.feat for c in cands] + [t.feat for t in targets if t.feat]
    sds = _sds(pool) if pool else []
    used, pairs, un = [], [], []
    for t in targets:
        if t.feat is None or t.net.get(window) is None:
            un.append({"ticker": tab.ticker, "t": t.idx, "reason": "no_history_or_outcome"})
            continue
        near = [c for c in cands if abs(c.idx - t.idx) <= lookaround
                and all(abs(c.idx - u) >= window for u in used)]
        if not near:
            un.append({"ticker": tab.ticker, "t": t.idx, "reason": "no_candidates"})
            continue
        best = None
        for c in near:
            z = [abs(a - b) / sd for a, b, sd in zip(t.feat, c.feat, sds)]
            if max(z) > caliper:
                continue
            dist = math.sqrt(sum(x * x for x in z))
            if best is None or dist < best[0]:
                best = (dist, c)
        if best is None:
            un.append({"ticker": tab.ticker, "t": t.idx, "reason": "caliper"})
            continue
        c = best[1]
        used.append(c.idx)
        pairs.append({"ticker": tab.ticker, "week": t.week, "flagged_t": t.idx,
                      "control_t": c.idx, "flagged_day": t.day, "control_day": c.day,
                      "diff": t.net[window] - c.net[window], "distance": best[0]})
    for d in tab.sealed_flagged:
        un.append({"ticker": tab.ticker, "t": None, "reason": "sealed"})
    return pairs, un


def match_all(tables, **kw):
    pairs, un = [], []
    for t in tables:
        p, u = match_controls(t, **kw)
        pairs += p
        un += u
    reasons = {}
    for u in un:
        reasons[u["reason"]] = reasons.get(u["reason"], 0) + 1
    return {"pairs": pairs, "unmatched": un, "n_unmatched": len(un), "reasons": reasons}


def boot_estimate(pairs, cluster="two_way", B=999, alpha=0.05, rng=None):
    """Mean diff with one-sided lower bound.  cluster: 'two_way' (multiplier
    bootstrap, independent Exp(1) weights on tickers and weeks) or 'ticker'
    (negative control only, not accepted by D4).  The bootstrap SE is inflated
    by sqrt(G/(G-1)) and the bound uses a t(G-1) critical value, G = number of
    clusters (the smaller of tickers and weeks for two-way): the raw percentile
    bound was anti-conservative with few distinct weeks (docs/43)."""
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
    two = cluster == "two_way"
    means = []
    for _ in range(B):
        a = [rng.expovariate(1.0) for _ in tk]
        b = [rng.expovariate(1.0) for _ in wk] if two else None
        num = den = 0.0
        for ti, wi, s, c in items:
            x = a[ti] * (b[wi] if two else 1.0)
            num += x * s
            den += x * c
        means.append(num / den if den else 0.0)
    G = len(tk) if not two else min(len(tk), len(wk))
    m = sum(means) / len(means)
    sd = math.sqrt(sum((x - m) ** 2 for x in means) / max(len(means) - 1, 1))
    se = sd * math.sqrt(G / (G - 1.0)) if G > 1 else float("inf")
    df = max(G - 1, 1)
    lower = mean - _t_quantile(1.0 - alpha, df) * se
    if se == 0 or se == float("inf"):
        p = 1.0 if mean <= 0 else (0.0 if se == 0 else 1.0)
    else:
        lo, hi = 1e-6, 0.999        # smallest level at which the lower bound is > 0
        if mean <= 0:
            p = 1.0
        else:
            for _ in range(40):
                mid = (lo + hi) / 2
                if mean - _t_quantile(1.0 - mid, df) * se > 0:
                    hi = mid
                else:
                    lo = mid
            p = hi
    return {"mean": mean, "lower": lower, "p": p, "n": len(pairs), "clusters": G}


def _t_quantile(q, df):
    """Student-t quantile (Cornish-Fisher expansion of the normal quantile)."""
    z = NormalDist().inv_cdf(q)
    return (z + (z ** 3 + z) / (4.0 * df)
            + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96.0 * df ** 2))


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


def balance_report(tables, pairs, window=10):
    """SMD (flagged minus comparison).  'before': flagged vs all eligible
    same-ticker candidates; 'after': matched pairs."""
    by = {t.ticker: t for t in tables}
    fl, ct, allc = [], [], []
    for p in pairs:
        t = by[p["ticker"]]
        fl.append(next(c.feat for c in t.flagged if c.idx == p["flagged_t"]))
        ct.append(next(c.feat for c in t.cands if c.idx == p["control_t"]))
    for t in tables:
        allc += [c.feat for c in t.cands if c.net.get(window) is not None]
    out = {}
    for j, name in enumerate(FEATURES):
        col = lambda rows: [r[j] for r in rows]
        out[name] = {"before": _smd(col(fl), col(allc)),
                     "after": _smd(col(fl), col(ct))}
    return out


def _read_rows(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def run_estimand(events_csv, prices_dir, windows=(5, 10, 21), flag_col=None,
                 B=999, seed=0, cost=COST, unseal_token=None, verbose=True):
    """Holm-adjusted results over the window family on the exploratory events file
    (columns of scripts/build_exploratory.py: ticker, date, decision_ts, ...).
    Every row is a posted ticker-day (used for the +/-10 day exclusion).  Flagged
    days are rows where `flag_col` is truthy; with flag_col=None all rows are
    flagged (event-versus-quiet-day contrast, not a model-flag verdict).
    Prints and returns aggregates only."""
    rows = _read_rows(events_csv)
    by = {}
    for r in rows:
        by.setdefault(r["ticker"], []).append(r)
    spy_path = os.path.join(prices_dir, "SPY.csv.gz")
    if not os.path.exists(spy_path):
        raise FileNotFoundError("SPY.csv.gz not found in prices_dir")
    bench = {"market": labels.load_prices(spy_path, "SPY")}
    tables, no_series = [], 0
    for tk in sorted(by):
        p = os.path.join(prices_dir, tk + ".csv.gz")
        try:
            ps = labels.load_prices(p, tk) if os.path.exists(p) else None
        except Exception:
            ps = None
        if ps is None or len(ps) == 0:
            no_series += len(by[tk])
            continue
        posted = {date.fromisoformat(r["date"][:10]) for r in by[tk]}
        flagged = {date.fromisoformat(r["date"][:10]) for r in by[tk]
                   if flag_col is None or str(r.get(flag_col, "")).lower() in ("1", "true")}
        tables.append(build_table(tk, ps, bench, posted, flagged, windows, cost,
                                  unseal_token))
    rng = random.Random(seed)
    res = []
    for w in windows:
        m = match_all(tables, window=w)
        est = boot_estimate(m["pairs"], "two_way", B=B, rng=rng)
        est.update(window=w, reasons=m["reasons"], n_flagged=sum(len(t.flagged) for t in tables))
        res.append(est)
    adj, rej = holm([r["p"] for r in res])
    for r, a, j in zip(res, adj, rej):
        r["p_holm"], r["reject"] = a, j
    if verbose:
        print("tickers=%d no_series_rows=%d" % (len(tables), no_series))
        for r in res:
            print("window=%d pairs=%d mean_net=%.4f lower95=%.4f p=%.3f p_holm=%.3f reject=%s "
                  "unmatched=%s" % (r["window"], r["n"], r["mean"], r["lower"], r["p"],
                                    r["p_holm"], r["reject"], r["reasons"]))
    return res
