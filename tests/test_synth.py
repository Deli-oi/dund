import random
from dund.synth import generate, cluster_permutation_pvalue


def _rate(n, rate, sims, seed0):
    c = 0
    for i in range(sims):
        d = generate(n, 0.05, rate, seed=seed0 + i)
        c += cluster_permutation_pvalue(d, 99, random.Random(i)) <= 0.05
    return c / sims


def test_null_false_positive_rate():
    fp = _rate(5000, None, 120, 10)
    assert fp <= 0.12  # nominal 0.05, tolerance for 120 sims


def test_large_lift_detected():
    assert _rate(10000, 0.20, 20, 500) >= 0.9


def test_regime_shift_kills_effect():
    d = generate(5000, 0.05, 0.5, regime_shift_day=0, seed=1)
    f = [h for h, fl in zip(d.hit, d.flag) if fl]
    assert sum(f) / len(f) < 0.2
