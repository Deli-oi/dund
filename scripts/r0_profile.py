"""R0 profile of one Arctic Shift submissions file (docs/14, docs/20).

Usage: python -I scripts/r0_profile.py PATH.zst [--subs subs.txt] [--out profile.json]

Streams the file, never unpacks it. Counts per subreddit and month, field presence,
GitHub-link and cashtag share, and retrieved_on lag. Downloads nothing.
Requires the optional 'ingest' extra (zstandard).
"""
import argparse
import collections
import datetime as dt
import io
import json
import re
import sys

GH = re.compile(r"github\.com/([\w.-]+)/([\w.-]+)", re.I)
CASHTAG = re.compile(r"(?<![\w$])\$[A-Z]{1,5}\b")


def open_lines(path):
    if path.endswith(".zst"):
        import zstandard
        fh = open(path, "rb")
        reader = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(fh)
        return io.TextIOWrapper(reader, encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--subs", help="file with one subreddit per line (case-insensitive)")
    ap.add_argument("--out", default="profile.json")
    a = ap.parse_args()
    keep = None
    if a.subs:
        keep = {l.strip().lower() for l in open(a.subs, encoding="utf-8") if l.strip()}
    per = collections.defaultdict(lambda: collections.Counter())
    fields = collections.Counter()
    lag = []
    n = 0
    for line in open_lines(a.path):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        n += 1
        sub = str(d.get("subreddit", "")).lower()
        if keep is not None and sub not in keep:
            continue
        for k in d:
            fields[k] += 1
        ts = d.get("created_utc")
        if ts is None:
            continue
        ym = dt.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m")
        c = per[(sub, ym)]
        c["posts"] += 1
        text = " ".join(str(d.get(k, "")) for k in ("title", "selftext", "url"))
        c["github"] += bool(GH.search(text))
        c["cashtag"] += bool(CASHTAG.search(text))
        c["removed"] += d.get("selftext") in ("[removed]", "[deleted]")
        if d.get("retrieved_on") and len(lag) < 50000:
            lag.append(int(d["retrieved_on"]) - int(ts))
    out = {
        "rows_read": n,
        "field_counts": dict(fields),
        "by_sub_month": {f"{s}|{m}": dict(c) for (s, m), c in sorted(per.items())},
        "retrieved_lag_median_s": sorted(lag)[len(lag) // 2] if lag else None,
    }
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"read {n} rows, wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
