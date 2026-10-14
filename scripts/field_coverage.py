"""Field coverage report for gzipped JSONL post census files.

Usage: python -I scripts/field_coverage.py DIR

Reads every *.jsonl.gz file in DIR (named {subreddit}_{YYYY-MM}.jsonl.gz),
skipping *.tmp files and files that fail to read. Prints a tab-separated table
with one row per (subreddit, year), followed by one 'ALL' row per year.
Percentages are the share of posts where the field is non-null and non-empty
(selftext also excludes '[removed]' and '[deleted]').
"""

import gzip
import json
import os
import re
import sys
from collections import defaultdict

FIELDS = [
    "author_created_utc",
    "subreddit_subscribers",
    "removed_by_category",
    "link_flair_text",
    "domain",
    "is_self",
    "author_flair_text",
    "num_crossposts",
    "upvote_ratio",
    "selftext",
]

FILE_RE = re.compile(r"^(?P<sub>.+)_(?P<year>\d{4})-(?P<month>\d{2})\.jsonl\.gz$")
SELFTEXT_EXCLUDE = {"[removed]", "[deleted]"}


def is_filled(key, value):
    if value is None:
        return False
    if isinstance(value, str):
        if value.strip() == "":
            return False
        if key == "selftext" and value in SELFTEXT_EXCLUDE:
            return False
        return True
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def read_file(path):
    """Return a list of parsed records, or raise on any read/parse failure."""
    records = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def new_counter():
    return {"n": 0, "filled": {f: 0 for f in FIELDS}}


def add_records(counter, records):
    for rec in records:
        if not isinstance(rec, dict):
            continue
        counter["n"] += 1
        for f in FIELDS:
            if is_filled(f, rec.get(f)):
                counter["filled"][f] += 1


def merge(into, other):
    into["n"] += other["n"]
    for f in FIELDS:
        into["filled"][f] += other["filled"][f]


def pct(part, whole):
    return "NA" if whole == 0 else f"{100.0 * part / whole:.1f}"


def main(argv):
    if len(argv) != 2:
        print("usage: python -I scripts/field_coverage.py DIR", file=sys.stderr)
        return 2
    root = argv[1]

    per_sub_year = defaultdict(new_counter)  # (subreddit, year) -> counter
    skipped = []

    for name in sorted(os.listdir(root)):
        if name.endswith(".tmp"):
            skipped.append((name, "tmp file"))
            continue
        m = FILE_RE.match(name)
        if not m:
            continue  # not a census file (e.g. manifest.tsv)
        path = os.path.join(root, name)
        try:
            records = read_file(path)
        except Exception as exc:  # unreadable or truncated gzip / bad JSON
            skipped.append((name, f"{type(exc).__name__}: {exc}"))
            continue
        add_records(per_sub_year[(m.group("sub"), m.group("year"))], records)

    for name, reason in skipped:
        print(f"skipped {name}: {reason}", file=sys.stderr)

    header = ["subreddit", "year", "posts"] + [f"{f}_%" for f in FIELDS]
    print("\t".join(header))

    for (sub, year) in sorted(per_sub_year):
        c = per_sub_year[(sub, year)]
        row = [sub, year, str(c["n"])] + [pct(c["filled"][f], c["n"]) for f in FIELDS]
        print("\t".join(row))

    all_by_year = defaultdict(new_counter)
    for (sub, year), c in per_sub_year.items():
        merge(all_by_year[year], c)
    for year in sorted(all_by_year):
        c = all_by_year[year]
        row = ["ALL", year, str(c["n"])] + [pct(c["filled"][f], c["n"]) for f in FIELDS]
        print("\t".join(row))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
