"""Post-level census over the full history, one gzipped JSONL per (subreddit, month).

Census rules (docs/22): date-ordered, no score filter, whole months, same fields for all subs.
Resumable: finished files are skipped. Writes to a .tmp then renames, so a kill never leaves a
partial file that looks complete. Stops if free disk drops under MIN_FREE_GB.

Usage: python -I scripts/census_posts.py OUT_DIR FIRST_YM LAST_YM sub1 sub2 ...
Months run in the order 2019, 2020, 2018, 2021, 2017, 2022, ... (pre-2021 first, docs/15).
"""
import calendar
import gzip
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://arctic-shift.photon-reddit.com/api/posts/search"
UA = "dund-research/0.1 (personal non-commercial research; elijahdalelio@gmail.com)"
# The API returns the full record when `fields` is omitted (the `fields` allow-list is narrower).
# Keep the columns the variable catalog (docs/19) can use; drop heavy presentation fields.
KEEP = ("id,created_utc,retrieved_on,retrieved_utc,subreddit,subreddit_id,subreddit_subscribers,"
        "author,author_fullname,author_created_utc,author_premium,author_flair_text,"
        "title,selftext,url,domain,is_self,is_original_content,is_video,over_18,spoiler,quarantine,"
        "link_flair_text,link_flair_template_id,score,ups,upvote_ratio,num_comments,num_crossposts,"
        "total_awards_received,gilded,distinguished,stickied,locked,pinned,edited,"
        "removed_by_category,removed_by,crosspost_parent,crosspost_parent_list").split(",")
MIN_FREE_GB = 0.6


def get(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    for attempt in range(10):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = json.loads(r.read().decode("utf-8"))
            if body.get("data") is not None:
                return body["data"]
            time.sleep(10 * (attempt + 1))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("x-ratelimit-reset", "20")) + 1)
            elif e.code >= 500 or e.code == 422:
                time.sleep(10 * (attempt + 1))
            else:
                raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("giving up: " + url)


def month_bounds(y, m):
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}-01", f"{ny:04d}-{nm:02d}-01"


def pull(sub, y, m, path):
    after, before = month_bounds(y, m)
    tmp = path.with_suffix(".tmp")
    seen = set()
    n = requests = 0
    cursor = after
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
        while True:
            data = get({"subreddit": sub, "after": cursor, "before": before,
                        "limit": 100, "sort": "asc"})
            requests += 1
            new = [d for d in data if d["id"] not in seen]
            for d in new:
                seen.add(d["id"])
                f.write(json.dumps({k: d[k] for k in KEEP if k in d}) + "\n")
            n += len(new)
            if not data or not new:
                break
            cursor = int(data[-1]["created_utc"])
            time.sleep(1.0)
    os.replace(tmp, path)
    return n, requests


def year_order(first, last):
    pref = [2019, 2020, 2018, 2021, 2017, 2022, 2016, 2023, 2015, 2024, 2014, 2025, 2013, 2026, 2012]
    seen = [y for y in pref if first <= y <= last]
    return seen + [y for y in range(first, last + 1) if y not in seen]


if __name__ == "__main__":
    out_dir, first, last, subs = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4:]
    fy, fm = map(int, first.split("-"))
    ly, lm = map(int, last.split("-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.tsv"
    for y in year_order(fy, ly):
        for m in range(1, 13):
            if (y, m) < (fy, fm) or (y, m) > (ly, lm):
                continue
            for sub in subs:
                path = out_dir / f"{sub}_{y:04d}-{m:02d}.jsonl.gz"
                if path.exists():
                    continue
                if shutil.disk_usage(out_dir).free / 1e9 < MIN_FREE_GB:
                    print("STOP: low disk", flush=True)
                    sys.exit(2)
                t0 = time.time()
                n, r = pull(sub, y, m, path)
                with manifest.open("a", encoding="utf-8") as mf:
                    mf.write(f"{sub}\t{y:04d}-{m:02d}\t{n}\t{r}\t{time.time() - t0:.0f}\t{path.stat().st_size}\n")
                print(f"{sub}\t{y:04d}-{m:02d}\tposts={n}\trequests={r}", flush=True)
    print("DONE", flush=True)
