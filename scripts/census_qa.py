"""QA report for the post census directory (gzipped JSONL, one file per subreddit-month).

Usage: python -I scripts/census_qa.py DATA_DIR [--list-missing]

Checks:
  1. Pairs (subreddit, month) in 2012-01..2026-09 with no finished .gz file, counted per year.
  2. Each finished .gz decompresses fully and its line count equals the manifest posts value.
  3. Duplicate ids within a file; created_utc outside the file's month (UTC).
  4. Gap candidates: month with zero posts whose previous and next month both have posts.
  5. Total posts and bytes per year.

*.tmp files are skipped. Nothing is written or deleted.
"""
import argparse
import calendar
import gzip
import json
import re
import sys
import zlib
from collections import defaultdict
from pathlib import Path

SUBS = [
    "wallstreetbets", "pennystocks", "investing", "ValueInvesting", "SecurityAnalysis",
    "smallcapstocks", "AMD_Stock", "biotech", "algotrading", "MachineLearning",
    "coolgithubprojects", "LocalLLaMA", "mcp", "OpenWebUI",
]
START = (2012, 1)
END = (2026, 9)
FILE_RE = re.compile(r"^(?P<sub>.+)_(?P<ym>\d{4}-\d{2})\.jsonl\.gz$")


def add_month(ym, k):
    y, m = int(ym[:4]), int(ym[5:7])
    idx = y * 12 + (m - 1) + k
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def month_range():
    out = []
    y, m = START
    while (y, m) <= END:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def month_bounds(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    lo = calendar.timegm((y, m, 1, 0, 0, 0, 0, 0, 0))
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    hi = calendar.timegm((ny, nm, 1, 0, 0, 0, 0, 0, 0))
    return lo, hi


def read_manifest(path):
    rows = defaultdict(list)
    bad = []
    with open(path, encoding="utf-8", newline="") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != 6:
                bad.append(f"line {n}: {len(parts)} fields")
                continue
            sub, month, posts, _requests, _seconds, nbytes = parts
            try:
                rows[(sub, month)].append({"posts": int(posts), "bytes": int(nbytes), "line": n})
            except ValueError:
                bad.append(f"line {n}: non-integer posts/bytes")
    return rows, bad


def check_file(path, ym):
    lo, hi = month_bounds(ym)
    res = {"lines": 0, "error": None, "bad_json": 0, "missing_id": 0, "missing_ts": 0,
           "dup_ids": 0, "dup_examples": [], "out_of_month": 0, "oom_examples": []}
    ids = set()
    try:
        with gzip.open(path, "rb") as f:
            for raw in f:
                if not raw.strip():
                    continue
                res["lines"] += 1
                try:
                    rec = json.loads(raw)
                except ValueError:
                    res["bad_json"] += 1
                    continue
                if not isinstance(rec, dict):
                    res["bad_json"] += 1
                    continue
                rid = rec.get("id")
                if rid is None:
                    res["missing_id"] += 1
                elif rid in ids:
                    res["dup_ids"] += 1
                    if len(res["dup_examples"]) < 3:
                        res["dup_examples"].append(str(rid))
                else:
                    ids.add(rid)
                ts = rec.get("created_utc")
                try:
                    ts = float(ts)
                except (TypeError, ValueError):
                    res["missing_ts"] += 1
                    continue
                if not (lo <= ts < hi):
                    res["out_of_month"] += 1
                    if len(res["oom_examples"]) < 3:
                        res["oom_examples"].append(f"{rid}@{int(ts)}")
    except (OSError, EOFError, zlib.error) as e:
        res["error"] = f"{type(e).__name__}: {e}"
    return res


def fmt(n):
    return f"{n:,}"


def main():
    ap = argparse.ArgumentParser(description="QA report for census gzipped JSONL files.")
    ap.add_argument("data_dir")
    ap.add_argument("--list-missing", action="store_true", help="print every missing pair")
    args = ap.parse_args()

    root = Path(args.data_dir)
    if not root.is_dir():
        print(f"Not a directory: {root}")
        return 2

    months = month_range()
    scope = {(s, m) for s in SUBS for m in months}

    files, tmp_skipped, other = {}, [], []
    for p in sorted(root.iterdir()):
        if not p.is_file() or p.name == "manifest.tsv":
            continue
        if p.name.lower().endswith(".tmp"):
            tmp_skipped.append(p.name)
            continue
        m = FILE_RE.match(p.name)
        if not m:
            other.append(p.name)
            continue
        key = (m.group("sub"), m.group("ym"))
        if key not in scope:
            other.append(p.name + " (out of scope)")
            continue
        files[key] = p

    manifest, manifest_bad = {}, []
    man_rows, manifest_bad = read_manifest(root / "manifest.tsv") if (root / "manifest.tsv").exists() else ({}, ["manifest.tsv missing"])
    man_dupes = []
    for key, rows in man_rows.items():
        if len(rows) > 1:
            man_dupes.append(f"{key[0]} {key[1]} ({len(rows)} rows)")
        manifest[key] = rows[0]
    man_out_scope = [k for k in manifest if k not in scope]

    missing = [(s, m) for m in months for s in SUBS if (s, m) not in files]

    # Verify every finished file.
    results = {}
    for key in sorted(files):
        results[key] = check_file(files[key], key[1])

    decomp_fail = [(k, r["error"], r["lines"]) for k, r in results.items() if r["error"]]
    count_mismatch = []
    for key, r in results.items():
        if r["error"] or key not in manifest:
            continue
        if r["lines"] != manifest[key]["posts"]:
            count_mismatch.append((key, manifest[key]["posts"], r["lines"]))
    no_file_in_manifest = [k for k in manifest if k in scope and k not in files]
    file_no_manifest = [k for k in files if k not in manifest]

    # Effective posts per pair: manifest value if present, else verified line count.
    eff = {}
    for key in scope:
        if key in manifest:
            eff[key] = manifest[key]["posts"]
        elif key in results and not results[key]["error"]:
            eff[key] = results[key]["lines"]
    gaps = []
    for s in SUBS:
        for m in months:
            if eff.get((s, m)) != 0 or (s, m) not in eff:
                continue
            prev_m, next_m = add_month(m, -1), add_month(m, 1)
            if eff.get((s, prev_m), 0) > 0 and eff.get((s, next_m), 0) > 0:
                gaps.append((s, m, eff[(s, prev_m)], eff[(s, next_m)]))

    print("=" * 72)
    print(f"Census QA: {root}")
    print("=" * 72)
    print(f"Finished .gz files: {len(files)}   manifest rows: {len(manifest)}   "
          f"in-scope pairs: {len(scope)}")
    print(f"Skipped *.tmp: {len(tmp_skipped)} {tmp_skipped if tmp_skipped else ''}")
    if other:
        print(f"Unrecognized or out-of-scope files: {len(other)} {other[:10]}")
    print()

    print("1. Pairs with no finished file, by year")
    per_year_missing = defaultdict(list)
    for s, m in missing:
        per_year_missing[m[:4]].append((s, m))
    for y in range(START[0], END[0] + 1):
        ys = str(y)
        expected = sum(1 for m in months if m[:4] == ys) * len(SUBS)
        n = len(per_year_missing.get(ys, []))
        print(f"   {ys}: {n:4d} missing of {expected}")
    print(f"   total missing: {len(missing)} of {len(scope)}")
    if args.list_missing:
        for ys in sorted(per_year_missing):
            print(f"   {ys}: " + ", ".join(f"{s} {m}" for s, m in per_year_missing[ys]))
    print()

    print("2. Decompression and line count vs manifest")
    print(f"   finished files checked: {len(results)}")
    print(f"   decompress failures: {len(decomp_fail)}")
    for k, err, lines in decomp_fail:
        print(f"     {k[0]} {k[1]}: {err} (read {lines} lines)")
    print(f"   line count != manifest posts: {len(count_mismatch)}")
    for (s, m), mp, lc in count_mismatch:
        print(f"     {s} {m}: manifest {mp}, file {lc}")
    print(f"   manifest rows with no finished file: {len(no_file_in_manifest)}")
    for s, m in no_file_in_manifest[:20]:
        print(f"     {s} {m}")
    print(f"   finished files with no manifest row: {len(file_no_manifest)}")
    for s, m in file_no_manifest[:20]:
        print(f"     {s} {m}")
    if manifest_bad:
        print(f"   manifest parse problems: {manifest_bad[:10]}")
    if man_dupes:
        print(f"   manifest duplicate keys: {man_dupes[:10]}")
    if man_out_scope:
        print(f"   manifest rows out of scope: {len(man_out_scope)}")
    print()

    print("3. Content checks")
    dup_files = [(k, r) for k, r in results.items() if r["dup_ids"]]
    oom_files = [(k, r) for k, r in results.items() if r["out_of_month"]]
    other_bad = [(k, r) for k, r in results.items()
                 if r["bad_json"] or r["missing_id"] or r["missing_ts"]]
    print(f"   files with duplicate ids: {len(dup_files)}  "
          f"(total duplicate rows: {sum(r['dup_ids'] for _, r in dup_files)})")
    for k, r in dup_files:
        print(f"     {k[0]} {k[1]}: {r['dup_ids']} dup, e.g. {r['dup_examples']}")
    print(f"   files with created_utc outside month: {len(oom_files)}  "
          f"(total rows: {sum(r['out_of_month'] for _, r in oom_files)})")
    for k, r in oom_files:
        print(f"     {k[0]} {k[1]}: {r['out_of_month']} rows, e.g. {r['oom_examples']}")
    if other_bad:
        print(f"   files with bad JSON / missing id / missing created_utc: {len(other_bad)}")
        for k, r in other_bad[:20]:
            print(f"     {k[0]} {k[1]}: json={r['bad_json']} id={r['missing_id']} ts={r['missing_ts']}")
    print()

    print("4. Gap candidates (zero posts between two months with posts)")
    print(f"   count: {len(gaps)}")
    for s, m, p, n in gaps:
        print(f"     {s} {m}: 0 posts (prev {p}, next {n})")
    print()

    print("5. Totals per year (posts = verified line count; bytes = on-disk .gz size)")
    print(f"   {'year':6}{'files':>7}{'posts':>14}{'bytes':>18}")
    grand_posts = grand_bytes = 0
    for y in range(START[0], END[0] + 1):
        ys = str(y)
        n_files = posts = nbytes = 0
        for (s, m), p in files.items():
            if m[:4] != ys:
                continue
            n_files += 1
            nbytes += p.stat().st_size
            r = results[(s, m)]
            if r["error"]:
                posts += manifest[(s, m)]["posts"] if (s, m) in manifest else 0
            else:
                posts += r["lines"]
        grand_posts += posts
        grand_bytes += nbytes
        print(f"   {ys:6}{n_files:7d}{fmt(posts):>14}{fmt(nbytes):>18}")
    print(f"   {'total':6}{len(files):7d}{fmt(grand_posts):>14}{fmt(grand_bytes):>18}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
