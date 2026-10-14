"""Build the exploratory label dataset for NON-sealed ticker-days (docs/42).

Usage: python -I build_exploratory.py TICKER_DAYS.csv.gz PRICES_DIR OUT_DIR
No models, no tests. Prints counts only. Sealed ticker-days are skipped, never priced.
Benchmark: SPY only (beta 1); no sector map is used.
"""
import csv
import gzip
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from dund.labels import hit_label, label_event, load_prices  # noqa: E402
from dund.sealed import is_sealed_event  # noqa: E402

COST = 0.0020
MAXWIN = 21
OUT_FIELDS = ["ticker", "date", "decision_ts", "entry_date", "car5", "car10", "car21",
              "net10", "placebo_pct10", "hit10", "reason", "has_series", "illiquid", "year", "subs"]
REASONS = ["no_series", "series_ended_early", "no_entry_near_ts", "insufficient_forward_window",
           "missing_benchmark", "illiquid", "other"]


def classify(reason):
    if not reason:
        return None
    r = reason.lower()
    if "no_series" in r:
        return "no_series"
    if "ended_early" in r or "delisted" in r:
        return "series_ended_early"
    if "no_entry" in r:
        return "no_entry_near_ts"
    if "insufficient_forward" in r:
        return "insufficient_forward_window"
    if "missing_benchmark" in r:
        return "missing_benchmark"
    if "illiquid" in r:
        return "illiquid"
    return "other"


def _f(x):
    return "" if x is None else repr(x)


def pct(a, b):
    return "%.1f%%" % (100.0 * a / b) if b else "n/a"


def process_row(row, series, bench):
    ts = datetime.fromisoformat(row["decision_ts"].replace("Z", "+00:00"))
    lab = label_event(row["ticker"], ts, series, bench)
    hit, why = hit_label(lab, window=10)

    def car(n):
        w = lab.windows.get(n)
        return w.car if w else None

    c10 = car(10)
    w10 = lab.windows.get(10)
    return {
        "ticker": row["ticker"], "date": row["date"], "decision_ts": row["decision_ts"],
        "entry_date": lab.entry_date.isoformat() if lab.entry_date else "",
        "car5": _f(car(5)), "car10": _f(c10), "car21": _f(car(21)),
        "net10": _f(None if c10 is None else c10 - COST),
        "placebo_pct10": _f(w10.placebo_percentile if w10 else None),
        "hit10": "" if hit is None else int(hit), "reason": why or "",
        "has_series": int(series is not None and len(series) > 0),
        "illiquid": int(lab.illiquid), "year": row["date"][:4], "subs": row.get("subs_json", ""),
    }, why


def build(ticker_days, prices_dir, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pd = Path(prices_dir)
    bench = {}
    spy = pd / "SPY.csv.gz"
    if spy.exists():
        bench = {"market": load_prices(str(spy), "SPY")}

    def get(t):
        p = pd / (t + ".csv.gz")
        try:
            return load_prices(str(p), t) if p.exists() else None
        except Exception:
            return None

    rows_by_ticker = defaultdict(list)
    n_sealed = 0
    with gzip.open(ticker_days, "rt", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if is_sealed_event(r["decision_ts"], MAXWIN):
                n_sealed += 1  # skipped before any price access
                continue
            rows_by_ticker[r["ticker"]].append(r)
    tot = defaultdict(int)
    by_year = defaultdict(lambda: defaultdict(int))
    by_sub = defaultdict(lambda: defaultdict(int))
    n = 0
    with gzip.open(out / "exploratory_events.csv.gz", "wt", newline="", encoding="utf-8") as fo:
        wr = csv.DictWriter(fo, OUT_FIELDS)
        wr.writeheader()
        for t in sorted(rows_by_ticker):
            s = get(t)  # one series in memory at a time
            for r in rows_by_ticker[t]:
                if bench:
                    rec, why = process_row(r, s, bench)
                else:
                    rec, why = process_row(r, None, {})
                    rec["reason"], why = "missing_benchmark", "missing_benchmark"
                wr.writerow({k: rec[k] for k in OUT_FIELDS})
                n += 1
                cat = classify(why)
                try:
                    subs = list(json.loads(r.get("subs_json") or "{}"))
                except Exception:
                    subs = []
                groups = [by_year[rec["year"]]] + [by_sub[x] for x in subs] + [tot]
                for g in groups:
                    g["n"] += 1
                    g["series"] += rec["has_series"]
                    g["illiq"] += rec["illiquid"]
                    if cat:
                        g["none"] += 1
                        g["r_" + cat] += 1
                    elif rec["hit10"] != "":
                        g["obs"] += 1
                        g["hit"] += int(rec["hit10"])
    write_coverage(out / "coverage.md", n, n_sealed, tot, by_year, by_sub)
    return n, n_sealed


def _table(title, groups):
    L = ["", "### " + title, "",
         "| group | n | with series | None | " + " | ".join(REASONS)
         + " | excluded by liquidity floors | observable | hit rate (observable) |",
         "|" + "---|" * (6 + len(REASONS))]
    for k in sorted(groups):
        g = groups[k]
        L.append("| %s | %d | %s | %s | %s | %s | %s | %s |" % (
            k, g["n"], pct(g["series"], g["n"]), pct(g["none"], g["n"]),
            " | ".join(pct(g["r_" + r], g["n"]) for r in REASONS),
            pct(g["illiq"], g["n"]), pct(g["obs"], g["n"]), pct(g["hit"], g["obs"])))
    return L


def write_coverage(path, n, n_sealed, tot, by_year, by_sub):
    obs, hit, none = tot["obs"], tot["hit"], tot["none"]
    lo = 100.0 * hit / n if n else 0.0          # unobservable as miss
    hi = 100.0 * (hit + none) / n if n else 0.0  # unobservable as hit
    L = ["# Exploratory coverage", "",
         "Benchmark: SPY only, beta 1 (no sector map). Cost 20 bps. Primary window 10 days.",
         "None is never a miss; the headline hit rate uses observable ticker-days only.", "",
         "- non-sealed ticker-days: %d" % n,
         "- sealed ticker-days skipped (prices never read): %d" % n_sealed,
         "- observable (hit is True/False): %d (%s)" % (obs, pct(obs, n)),
         "- unobservable (None): %d (%s)" % (none, pct(none, n)),
         "- headline hit rate, observable only: %s" % pct(hit, obs),
         "- worst-case bounds, unobservable as miss / as hit: %.1f%% / %.1f%%" % (lo, hi)]
    L += _table("By year", by_year) + _table("By sub (ticker-day counted once per sub)", by_sub)
    Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv):
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    n, ns = build(argv[1], argv[2], argv[3])
    print("non-sealed ticker-days: %d; sealed skipped: %d" % (n, ns))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
