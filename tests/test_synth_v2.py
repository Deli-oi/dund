import random
from dund.synth import generate_v2, boot_lower_bounds


def _rej(n_flag, edge, sims, seed0, key, rate=0.005):
    c = 0
    for i in range(sims):
        d = generate_v2(n_flag, rate, edge, seed=seed0 + i)
        c += boot_lower_bounds(d, 99, random.Random(i))[key] > 0
    return c / sims


def test_two_way_null_false_positives_in_tolerance():
    assert _rej(200, 0.0, 200, 1000, "two_way") <= 0.11


def test_ticker_only_inflated_under_week_shock():
    t = _rej(200, 0.0, 200, 1000, "ticker")
    w = _rej(200, 0.0, 200, 1000, "two_way")
    assert t > 0.15 and t > w + 0.08


def test_large_edge_detected():
    assert _rej(400, 300.0, 40, 5000, "two_way") >= 0.9


def test_regime_break_removes_edge():
    a = generate_v2(2000, 0.005, 1000.0, seed=3)
    b = generate_v2(2000, 0.005, 1000.0, seed=3, regime_break=True)
    assert sum(a.d) / len(a.d) > sum(b.d) / len(b.d) + 0.003
