import random

from dund.controls import (Series, match_controls, boot_estimate, holm,
                           balance_report, features)


def make(ticker, n=200, seed=0, flagged=(100,), edge=0.0, W=10, shock=None):
    r = random.Random(seed)
    ret = [r.gauss(0, 0.01) for _ in range(n)]
    vol = [1000 + r.random() * 200 for _ in range(n)]
    men = [r.randint(0, 3) for _ in range(n)]
    ar = [r.gauss(0, 0.01) for _ in range(n)]
    for f in flagged:
        for k in range(W):
            if f + k < n:
                ar[f + k] += edge / W
    week = [i // 5 for i in range(n)]
    if shock:
        for i in range(n):
            ar[i] += shock[week[i] % len(shock)] / 5
    return Series(ticker, ret, vol, men, ar, week, set(flagged))


def test_no_lookahead():
    s = make("A")
    s2 = make("A")
    for i in range(100, 110):          # change data from decision time onward
        s2.ret[i] += 5.0
        s2.vol[i] *= 50
        s2.mentions[i] += 99
    assert features(s, 100) == features(s2, 100)
    p1, _ = match_controls(s, caliper=3.0)
    p2, _ = match_controls(s2, caliper=3.0)
    assert [p["control_t"] for p in p1 if p["control_t"] + 10 <= 100] == \
           [p["control_t"] for p in p2 if p["control_t"] + 10 <= 100]
    # a control chosen before t has features/outcome unaffected by later data
    s3 = make("A")
    for i in range(101, 200):
        s3.ret[i] += 1.0
    assert features(s, 100) == features(s3, 100)


def test_no_overlap_and_exclusion():
    s = make("A", flagged=(60, 100, 140))
    s.posted = {20}
    pairs, _ = match_controls(s, caliper=5.0)
    cs = sorted(p["control_t"] for p in pairs)
    assert cs
    assert all(b - a >= 10 for a, b in zip(cs, cs[1:]))
    for c in cs:
        assert all(abs(c - e) > 10 for e in (60, 100, 140, 20))


def test_caliper():
    s = make("A", flagged=(100,))
    s.ret[95:100] = [0.5] * 5
    pairs, un = match_controls(s, caliper=0.5)
    assert not pairs and un[0]["reason"] == "caliper"
    pairs, _ = match_controls(s, caliper=100.0)
    assert len(pairs) == 1


def _pairs(edge, seed, nt=30, shock=None):
    out = []
    for i in range(nt):
        s = make("T%d" % i, seed=seed * 1000 + i, flagged=(60, 100, 140),
                 edge=edge, shock=shock)
        p, _ = match_controls(s, caliper=3.0)
        out += p
    return out


def test_recovers_edge():
    est = boot_estimate(_pairs(0.03, 1), B=199, rng=random.Random(1))
    assert 0.015 < est["mean"] < 0.045
    assert est["lower"] > 0


def test_null_false_positive_rate():
    rej = 0
    R = 60
    for k in range(R):
        est = boot_estimate(_pairs(0.0, k + 10, nt=20), B=99, rng=random.Random(k))
        rej += est["lower"] > 0
    assert rej / R < 0.2


def test_two_way_wider_with_weekly_shock():
    pairs = _pairs(0.0, 3, nt=30, shock=[0.05, -0.05, 0.0, 0.08, -0.08, 0.02, -0.02])
    two = boot_estimate(pairs, "two_way", B=299, rng=random.Random(2))
    one = boot_estimate(pairs, "ticker", B=299, rng=random.Random(2))
    assert (two["mean"] - two["lower"]) > (one["mean"] - one["lower"])


def test_holm_and_balance():
    adj, rej = holm([0.01, 0.04, 0.03])
    assert abs(adj[0] - 0.03) < 1e-12 and rej == [True, False, False]
    s = make("A", flagged=(60, 100, 140))
    p, _ = match_controls(s, caliper=3.0)
    rep = balance_report([s], p)
    assert set(rep) == {"r5", "r21", "volratio", "vol21", "mentions"}
