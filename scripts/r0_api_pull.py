"""R0 pilot pull: full-month census of posts per subreddit from the Arctic Shift API.

Census rules (docs/22): date-ordered, no score filter, whole month, same fields for all subs.
Usage: python -I scripts/r0_api_pull.py OUT_DIR YYYY-MM sub1 sub2 ...
Polite: descriptive User-Agent, 1 s pause, honors 429 reset headers.
"""
import calendar
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://arctic-shift.photon-reddit.com/api/posts/search"
UA = "dund-research/0.1 (personal non-commercial research; elijahdalelio@gmail.com)"
FIELDS = ("id,created_utc,retrieved_on,subreddit,author,title,selftext,url,"
          "score,num_comments,link_flair_text,over_18")


def get(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    for attempt in range(8):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = json.loads(r.read().decode("utf-8"))
            if body.get("data") is None:
                if "not a valid field" in str(body.get("error")):
                    raise ValueError(body["error"])
                time.sleep(10 * (attempt + 1))
                continue
            return body
        except urllib.error.HTTPError as e:
            wait = 20
            if e.code == 429:
                wait = int(e.headers.get("x-ratelimit-reset", "20")) + 1
            elif e.code >= 500 or e.code == 422:
                wait = 10 * (attempt + 1)
            else:
                raise
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("giving up: " + url)


def month_bounds(ym):
    y, m = map(int, ym.split("-"))
    last = calendar.monthrange(y, m)[1]
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}-01", f"{ny:04d}-{nm:02d}-01"


def pull(sub, ym, out_dir):
    after, before = month_bounds(ym)
    path = Path(out_dir) / f"{sub}_{ym}.jsonl"
    seen = set()
    n = requests = 0
    cursor = after
    with path.open("w", encoding="utf-8") as f:
        while True:
            data = get({"subreddit": sub, "after": cursor, "before": before,
                        "limit": 100, "sort": "asc", "fields": FIELDS})["data"]
            requests += 1
            new = [d for d in data if d["id"] not in seen]
            for d in new:
                seen.add(d["id"])
                f.write(json.dumps(d) + "\n")
            n += len(new)
            if not data or not new:
                break
            cursor = int(data[-1]["created_utc"])
            time.sleep(1.0)
    return n, requests


if __name__ == "__main__":
    out_dir, ym, subs = sys.argv[1], sys.argv[2], sys.argv[3:]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for s in subs:
        n, r = pull(s, ym, out_dir)
        print(f"{s}\t{ym}\tposts={n}\trequests={r}", flush=True)
