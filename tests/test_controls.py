import math
import multiprocessing as mp
import os
import random
from datetime import date, datetime, timedelta, timezone

import pytest

from dund import labels
from dund.controls import (COST, Cand, Table, balance_report, boot_estimate, build_table,
                           decision_ts, features_at, holm, match_all, match_controls,
                           momentum_gate, net_outcomes)
from dund.labels import PriceSeries
from dund.sealed import UNSEAL_TOKEN


def _weekdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def world(seed=0, n=260, start=date(2024, 1, 2), edge=0.0, flag_idx=(120,)):
    r = random.Random(seed)
    ds = _weekdays(start, n)
    px, vol = [100.0], [2e6 * (1 + 0.2 * r.random()) for _ in range(n)]
    ar = [0.0] + [r.gauss(0, 0.01) for _ in range(n - 1)]
    for f in flag_idx:       # edge realised over the 10 days after the entry close
        for k in range(1, 11):
            if f + k < n:
                ar[f + k] += edge / 10
    for i in range(1, n):
        px.append(px[-1] * (1 + ar[i]))
    stock = PriceSeries("AAA", ds, px, px, vol)
    flat = [100.0] * n
    spy = PriceSeries("SPY", ds, flat, flat, [1e7] * n)
    return stock, {"market": spy}, ds


def test_decision_and_entry_use_labels():
    ps, _, ds = world()
    d = ds[100]                                   # a weekday
    assert decision_ts(d) == datetime.combine(d + timedelta(days=1), datetime.min.time(),
                                              tzinfo=timezone.utc)
    i0 = labels.entry_index(ps, decision_ts(d))
    nxt = d + timedelta(days=1)
    assert ps.dates[i0] >= nxt                    # entry is a later close, never d itself


def test_features_use_only_prior_data():
    ps, _, ds = world()
    i0 = labels.entry_index(ps, decision_ts(ds[100]))
    f1 = features_at(ps, i0, ds[100], set())
    ps2 = PriceSeries("AAA", ps.dates, list(ps.close), list(ps.adj_close), list(ps.volume))
    for j in range(i0, len(ps2)):                 # corrupt everything from entry on
        ps2.adj_close[j] *= 7.0
        ps2.volume[j] *= 50
    assert features_at(ps2, i0, ds[100], set()) == f1
    # posts dated on or after d never count
    assert features_at(ps, i0, ds[100], {ds[100], ds[100] + timedelta(days=1)})[4] == 0.0
    assert features_at(ps, i0, ds[100], {ds[100] - timedelta(days=2)})[4] == 1.0


def test_outcome_equals_label_event_net_of_cost():
    ps, bench, ds = world(edge=0.05)
    d = ds[120]
    out, lab = net_outcomes("AAA", d, ps, bench, (5, 10, 21))
    lab2 = labels.label_event("AAA", decision_ts(d), ps, bench)   # default full call
    for w in (5, 10, 21):
        assert out[w] == pytest.approx(lab2.windows[w].car - COST)
    i0 = labels.entry_index(ps, decision_ts(d))
    assert lab.windows[10].car == pytest.approx(ps.adj_close[i0 + 10] / ps.adj_close[i0] - 1.0)


def test_controls_exclude_events_and_sealed():
    ps, bench, ds = world(flag_idx=())
    posted = {ds[60], ds[150]}
    tab = build_table("AAA", ps, bench, posted | {ds[100]}, {ds[100]}, windows=(10,))
    ev = set(tab.posted_idx)
    assert len(ev) == 3 and tab.cands
    for c in tab.cands:
        assert all(abs(c.idx - e) > 10 for e in ev)
    # sealed block A (2020): nothing is eligible without the token, flagged day is reported
    ps2, bench2, ds2 = world(start=date(2020, 3, 2), flag_idx=())
    t2 = build_table("AAA", ps2, bench2, {ds2[100]}, {ds2[100]}, windows=(10,))
    assert not t2.cands and not t2.flagged and len(t2.sealed_flagged) == 1
    t3 = build_table("AAA", ps2, bench2, {ds2[100]}, {ds2[100]}, windows=(10,),
                     unseal_token=UNSEAL_TOKEN)
    assert t3.cands and t3.flagged
    # a control whose window straddles into a sealed block is dropped too
    ps4, bench4, ds4 = world(start=date(2019, 8, 1), n=130, flag_idx=())
    t4 = build_table("AAA", ps4, bench4, set(), set(), windows=(10,))
    assert all(c.day < date(2019, 12, 1) - timedelta(days=21) for c in t4.cands)


def test_matching_pairs_and_balance():
    ps, bench, ds = world(edge=0.06, flag_idx=(100, 160))
    tab = build_table("AAA", ps, bench, {ds[100], ds[160]}, {ds[100], ds[160]}, windows=(10,))
    pairs, un = match_controls(tab, 10, caliper=3.0)
    assert pairs
    cs = sorted(p["control_t"] for p in pairs)
    assert all(b - a >= 10 for a, b in zip(cs, cs[1:]))
    assert all(abs(p["control_t"] - p["flagged_t"]) <= 40 for p in pairs)
    rep = balance_report([tab], pairs)
    assert set(rep) == {"r5", "r21", "volratio", "vol21", "mentions"}
    tight, un2 = match_controls(tab, 10, caliper=1e-9)
    assert not tight and un2[0]["reason"] == "caliper"


def test_holm():
    adj, rej = holm([0.01, 0.04, 0.03])
    assert abs(adj[0] - 0.03) < 1e-12 and rej == [True, False, False]


# ---------------- calibration in a null world with a weekly shock ----------------

N_TICK, N_DAY, N_FLAG_WEEKS, SHOCK_SD, IDIO_SD = 30, 250, 8, 0.03, 0.03
B_BOOT = 199


def null_world_tables(seed, edge=0.0):
    """No flagged edge.  A market-wide weekly shock hits every ticker's abnormal
    return, and flagged days of all tickers cluster in a few shared weeks."""
    r = random.Random(seed)
    nweek = N_DAY // 5 + 3
    shock = [r.gauss(0, SHOCK_SD) for _ in range(nweek)]
    fweeks = r.sample(range(10, N_DAY // 5 - 8), N_FLAG_WEEKS)
    tables = []
    for k in range(N_TICK):
        def cand(i):
            w = i // 5
            # 10-day outcome spans two weeks of shock
            y = shock[w] + shock[w + 1] + r.gauss(0, IDIO_SD)
            return Cand(i, date(2024, 1, 1) + timedelta(days=i), (2024, w),
                        [r.gauss(0, 1) for _ in range(5)], {10: y})
        fl_idx = sorted({5 * w + r.randrange(5) for w in fweeks if r.random() < 0.7})
        flagged = [cand(i) for i in fl_idx]
        for c in flagged:
            c.net[10] += edge
        cands = [cand(i) for i in range(31, N_DAY - 10)
                 if all(abs(i - f) > 10 for f in fl_idx)]
        tables.append(Table("T%d" % k, cands, flagged, fl_idx))
    return tables


def _one_rep(seed):
    tabs = null_world_tables(seed)
    pairs = match_all(tabs, window=10, caliper=3.0)["pairs"]
    two = boot_estimate(pairs, "two_way", B=B_BOOT, rng=random.Random(seed))
    one = boot_estimate(pairs, "ticker", B=B_BOOT, rng=random.Random(seed))
    return two["lower"] > 0, one["lower"] > 0


def _mc_interval(k, n):
    p = k / n
    se = math.sqrt(p * (1 - p) / n)
    return p, max(0.0, p - 1.96 * se), p + 1.96 * se


def test_null_calibration_two_way_vs_ticker_only():
    reps = 1000
    t_workers = max(1, min(8, os.cpu_count() or 1))
    if t_workers > 1:
        with mp.Pool(t_workers) as pool:
            out = pool.map(_one_rep, range(1000, 1000 + reps), chunksize=10)
    else:
        out = [_one_rep(s) for s in range(1000, 1000 + reps)]
    p2, lo2, hi2 = _mc_interval(sum(o[0] for o in out), reps)
    p1, lo1, hi1 = _mc_interval(sum(o[1] for o in out), reps)
    print("two-way FPR %.3f [%.3f, %.3f]; ticker-only FPR %.3f [%.3f, %.3f]"
          % (p2, lo2, hi2, p1, lo1, hi1))
    assert 0.01 <= p2 <= 0.08
    assert p1 > 0.08
    assert p1 > p2


def test_recovers_edge():
    tabs = null_world_tables(5, edge=0.08)
    pairs = match_all(tabs, window=10, caliper=3.0)["pairs"]
    est = boot_estimate(pairs, B=199, rng=random.Random(1))
    assert 0.04 < est["mean"] < 0.12 and est["lower"] > 0


def test_run_estimand_smoke(tmp_path, capsys):
    import csv
    import gzip
    from dund.controls import run_estimand
    ps, bench, ds = world(seed=3, edge=0.05, flag_idx=(100, 160))

    def dump(name, s):
        with gzip.open(tmp_path / (name + ".csv.gz"), "wt", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "close", "adj_close", "volume"])
            for d, c, a, v in zip(s.dates, s.close, s.adj_close, s.volume):
                w.writerow([d.isoformat(), c, a, v])
    dump("AAA", ps)
    dump("SPY", bench["market"])
    ev = tmp_path / "ev.csv"
    with open(ev, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", "date", "decision_ts"])
        for i in (100, 160):
            d = ds[i]
            w.writerow(["AAA", d.isoformat(), decision_ts(d).isoformat()])
    res = run_estimand(str(ev), str(tmp_path), B=99)
    assert [r["window"] for r in res] == [5, 10, 21]
    assert all("p_holm" in r for r in res)
    assert "AAA" not in capsys.readouterr().out.replace("no_series", "")


# ---------------- momentum gate ----------------

def _gate_world(runup=0.0, at=150, n=260):
    r = random.Random(11)
    ds = _weekdays(date(2024, 1, 2), n)
    ar = [0.0] + [r.gauss(0, 0.01) for _ in range(n - 1)]
    for k in range(1, 6):          # run-up over the 5 closes before entry `at`
        ar[at - k] += runup / 5
    px = [100.0]
    for i in range(1, n):
        px.append(px[-1] * (1 + ar[i]))
    flat = [100.0] * n
    return (PriceSeries("AAA", ds, px, px, [2e6] * n),
            {"market": PriceSeries("SPY", ds, flat, flat, [1e7] * n)})


def test_gate_runup_out_quiet_passes():
    ps, b = _gate_world(runup=0.4)
    assert momentum_gate(ps, b, 150) == "out"
    ps, b = _gate_world(runup=0.0)
    assert momentum_gate(ps, b, 150) == "pass"


def test_gate_no_lookahead():
    ps, b = _gate_world(runup=0.4)
    base = momentum_gate(ps, b, 150)
    ps2 = PriceSeries("AAA", ps.dates, list(ps.close), list(ps.adj_close), list(ps.volume))
    for j in range(150, len(ps2)):
        ps2.adj_close[j] *= 3.0
    assert momentum_gate(ps2, b, 150) == base


def test_gate_unknown_and_counts():
    ps, b = _gate_world()
    assert momentum_gate(ps, b, 40) == "unknown"
    tab = build_table("AAA", ps, b, {ps.dates[150]}, {ps.dates[150]}, windows=(10,))
    tab.flagged[0].gate = "out"
    pairs, un = match_controls(tab, 10, caliper=3.0)
    assert not pairs and un[0]["reason"] == "gate_out"
    assert match_all([tab], window=10, caliper=3.0)["gate"]["flagged_out"] == 1
    pairs, _ = match_controls(tab, 10, caliper=3.0, momentum_gate=False)
    assert pairs
