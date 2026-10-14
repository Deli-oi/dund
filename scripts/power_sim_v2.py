"""Power simulation v2 for the REAL estimand (docs/38 D1/D4/D8).
Net 10-day abnormal return of flagged ticker-days minus matched-control mean,
one-sided lower bound > 0 under ticker-only (negative control), week-only and
two-way (ticker x calendar week) clustered bootstrap.
Usage: python scripts/power_sim_v2.py [null_sims=2000] [power_sims=200]
The old flagged-vs-base-rate simulation is scripts/power_sim.py (detection check)."""
import math, os, random, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from dund.synth import generate_v2, boot_lower_bounds

RATES = [0.005, 0.001, 0.02]
EDGES = [50, 100, 200, 300]
NF_GRID = [25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600]
METHODS = ["ticker", "week", "two_way"]


def one(args):
    n_flag, rate, edge, seed, regime = args
    d = generate_v2(n_flag, rate, edge, seed=seed, regime_break=regime)
    lb = boot_lower_bounds(d, 99, random.Random(seed ^ 0x5bd1))
    return [lb[m] > 0 for m in METHODS]


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def power_curve(args):
    """Sequential in n_flag until two-way power >= 0.95. Returns rows."""
    rate, edge, sims, regime = args
    rows = []
    for nf in NF_GRID:
        hits = [0, 0, 0]
        for i in range(sims):
            r = one((nf, rate, edge, 7_000_000 + nf * 1000 + i, regime))
            for j in range(3):
                hits[j] += r[j]
        rows.append((nf, [h / sims for h in hits]))
        if hits[2] / sims >= 0.95:
            break
    return (rate, edge, regime, rows)


def n_for_80(rows, col=2):
    prev = None
    for nf, p in rows:
        if p[col] >= 0.8:
            if prev is None:
                return nf
            (a, pa), (b, pb) = prev, (nf, p[col])
            la, lb_ = math.log(a), math.log(b)
            return math.exp(la + (lb_ - la) * (0.8 - pa) / (pb - pa))
        prev = (nf, p[col])
    return None


def main():
    nulls = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    sims = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    t0 = time.time()
    with Pool() as pool:
        print("## (a) False positives at edge 0 (alpha 0.05 one-sided), %d null sims" % nulls)
        print("| flag rate | n_flag | N | ticker-only | week-only | two-way |")
        print("|---|---|---|---|---|---|")
        for rate in RATES:
            for nf in (100, 400):
                jobs = [(nf, rate, 0.0, 100 + i, False) for i in range(nulls)]
                res = pool.map(one, jobs, chunksize=20)
                cells = []
                for j in range(3):
                    k = sum(r[j] for r in res)
                    lo, hi = wilson(k, nulls)
                    cells.append("%.3f [%.3f, %.3f]" % (k / nulls, lo, hi))
                print("| %.1f%% | %d | %d | %s |" % (rate * 100, nf, round(nf / rate), " | ".join(cells)), flush=True)
        jobs = [(r, e, sims, False) for r in RATES for e in EDGES]
        jobs += [(0.005, e, sims, True) for e in EDGES]  # regime break option
        curves = pool.map(power_curve, jobs, chunksize=1)
    print("\n## (b,c) Units for 80%% power (%d sims per grid point)" % sims)
    print("| regime break | flag rate | net edge bps | flagged units (two-way) | ticker-days N | years at 20k/yr | flagged (week-only) | flagged (ticker-only) |")
    print("|---|---|---|---|---|---|---|---|")
    for rate, edge, regime, rows in curves:
        nf, nw, nt = n_for_80(rows, 2), n_for_80(rows, 1), n_for_80(rows, 0)
        f = lambda x: ">25600" if x is None else "%d" % round(x)
        if nf is None:
            Ns, yrs = ">%d" % round(NF_GRID[-1] / rate), "n/a"
        else:
            Ns, yrs = "%d" % round(nf / rate), "%.1f" % (nf / rate / 20000)
        print("| %s | %.1f%% | %d | %s | %s | %s | %s | %s |" % (
            "yes" if regime else "no", rate * 100, edge, f(nf), Ns, yrs, f(nw), f(nt)))
    print("\ntime=%.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
