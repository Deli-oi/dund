"""Power / false-positive simulation for the clustered permutation test.
Usage: python scripts/power_sim.py [n_sims]   (default 500)"""
import os, random, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from dund.synth import generate, cluster_permutation_pvalue

NS = [2000, 5000, 10000, 20000, 40000]
LIFTS = [("null 5%->5%", 0.05), ("5%->7%", 0.07), ("5%->10%", 0.10), ("5%->15%", 0.15)]
ALPHA = 0.05


def one(args):
    n, rate, seed = args
    d = generate(n, 0.05, rate, seed=seed)
    return cluster_permutation_pvalue(d, 199, random.Random(seed)) <= ALPHA


def main():
    sims = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    t0 = time.time()
    res = {}
    with Pool() as pool:
        for name, rate in LIFTS:
            for n in NS:
                jobs = [(n, rate, 1000 * n + i + int(rate * 1e4)) for i in range(sims)]
                res[(name, n)] = sum(pool.map(one, jobs, chunksize=10)) / sims
    print(f"sims={sims} alpha={ALPHA} flag_rate=0.02 time={time.time()-t0:.0f}s")
    print("| scenario | " + " | ".join(f"N={n}" for n in NS) + " |")
    print("|---|" + "---|" * len(NS))
    for name, _ in LIFTS:
        print(f"| {name} | " + " | ".join(f"{res[(name,n)]:.3f}" for n in NS) + " |")
    print("\nN for 80% power (linear interp):")
    for name, _ in LIFTS[1:]:
        pw = [res[(name, n)] for n in NS]
        out = ">%d" % NS[-1]
        if pw[0] >= .8:
            out = "<=%d" % NS[0]
        else:
            for i in range(1, len(NS)):
                if pw[i] >= .8:
                    a, b = pw[i-1], pw[i]
                    out = "~%d" % round(NS[i-1] + (NS[i]-NS[i-1]) * (.8-a)/(b-a), -2)
                    break
        print(f"| {name} | {out} |")


if __name__ == "__main__":
    main()
