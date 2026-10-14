"""Build ticker-day and repo-mention tables from finished census files.

Usage: python -I build_ticker_days.py IN_DIR OUT_DIR [TICKERS_CSV]
OUT_DIR must be new/empty or absent. Skips *.tmp. Streams month by month,
sorting each month's items by time (single pass, no look-ahead).
"""
import csv
import gzip
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dund.entities import EntityResolver, TickerTable  # noqa: E402
from dund.ticker_days import REPO_FIELDS, TICKER_DAY_FIELDS, TickerDayAggregator  # noqa: E402
from dund.schema import get_salt  # noqa: E402
from dund.transform import iter_census, to_item  # noqa: E402

DEFAULT_TICKERS = r"C:\Users\dalele\dund-data\entities\sec_20261014\out\tickers.csv"
NAME_RE = re.compile(r"^(.+)_(\d{4}-\d{2})\.jsonl\.gz$")


def main(in_dir, out_dir, tickers=DEFAULT_TICKERS):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        print("refusing: output directory not empty", file=sys.stderr)
        return 1
    months = defaultdict(list)
    for p in Path(in_dir).iterdir():
        m = NAME_RE.match(p.name)
        if m:
            months[m.group(2)].append(p)
    salt = get_salt()  # raises if DUND_SALT is unset (D13); no fallback
    agg = TickerDayAggregator(EntityResolver(TickerTable.from_csv(tickers)))
    nfiles = nbad = 0
    with gzip.open(out / "ticker_days.csv.gz", "wt", newline="", encoding="utf-8") as ft, \
         gzip.open(out / "repo_mentions.csv.gz", "wt", newline="", encoding="utf-8") as fr:
        wt = csv.DictWriter(ft, TICKER_DAY_FIELDS)
        wt.writeheader()
        wr = csv.DictWriter(fr, REPO_FIELDS)
        wr.writeheader()

        def emit(res):
            wt.writerows(res[0])
            wr.writerows(res[1])

        for month in sorted(months):
            items = []
            for p in sorted(months[month]):
                nfiles += 1
                for raw in iter_census(p):
                    try:
                        items.append(to_item(raw, "ticker_days_v1", salt))
                    except ValueError:
                        nbad += 1
            items.sort(key=lambda i: (i.created_at, i.item_id))
            for it in items:
                emit(agg.add(it))
        emit(agg.finish())

    s = agg.stats
    print(f"files={nfiles} months={len(months)} bad_records={nbad}")
    print("\n## Per year: ticker-days, distinct tickers, top-10 share of mentions")
    print("year | ticker_days | distinct_tickers | top10_share")
    for y in sorted(s["tickerdays_by_year"]):
        c = s["mentions_by_year"][y]
        tot = sum(c.values())
        top = sum(n for _, n in c.most_common(10))
        print(f"{y} | {s['tickerdays_by_year'][y]} | {len(s['tickers_by_year'][y])} | {top / tot:.1%}")
    print("\n## Ticker-days per sub-year (days with >=1 post in sub)")
    print("sub | year | ticker_days")
    for (sub, y), n in sorted(s["tickerdays_by_sub_year"].items()):
        print(f"{sub} | {y} | {n}")
    print("\n## Resolved-post share per sub-year (>=1 stock candidate)")
    print("sub | year | posts | resolved | share")
    for (sub, y), n in sorted(s["posts"].items()):
        r = s["resolved"][(sub, y)]
        print(f"{sub} | {y} | {n} | {r} | {r / n:.1%}")
    print(f"\nout={out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: build_ticker_days.py IN_DIR OUT_DIR [TICKERS_CSV]")
    sys.exit(main(*sys.argv[1:]))
