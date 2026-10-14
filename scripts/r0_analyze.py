import collections
import datetime as dt
import glob
import json
import os
import re
import statistics
import sys

D = sys.argv[1]
GH = re.compile(r"github\.com/([\w.-]+)/([\w.-]+)", re.I)
TAG = re.compile(r"(?<![\w$])\$([A-Za-z]{1,5})\b")
rows = {}
for f in sorted(glob.glob(os.path.join(D, "*_2026-08.jsonl"))):
    sub = os.path.basename(f).split("_")[0]
    rows[sub] = [json.loads(l) for l in open(f, encoding="utf-8")]

print(f"{'sub':18s}{'posts':>6s}{'/day':>6s}{'auth':>6s}{'top5%':>6s}{'gh%':>5s}{'tag%':>5s}"
      f"{'rem%':>5s}{'selfEmpty%':>11s}{'score<=1%':>10s}{'medCom':>7s}{'flair%':>7s}{'lag_s':>8s}{'zeroDays':>9s}")
tot = collections.Counter()
alltags = collections.Counter()
allrepos = collections.Counter()
hours = collections.Counter()
for sub, rs in rows.items():
    n = len(rs)
    days = collections.Counter(dt.datetime.utcfromtimestamp(r["created_utc"]).strftime("%d") for r in rs)
    auth = collections.Counter(r.get("author") for r in rs)
    top = sorted(auth.values(), reverse=True)
    k = max(1, int(0.05 * len(auth)))
    top5 = sum(top[:k]) / n
    text = [" ".join(str(r.get(k_) or "") for k_ in ("title", "selftext", "url")) for r in rs]
    gh = sum(bool(GH.search(t)) for t in text) / n
    tag = sum(bool(TAG.search(t)) for t in text) / n
    rem = sum((r.get("selftext") in ("[removed]", "[deleted]")) or r.get("author") == "[deleted]" for r in rs) / n
    se = sum(not (r.get("selftext") or "").strip() for r in rs) / n
    s1 = sum((r.get("score") or 0) <= 1 for r in rs) / n
    mc = statistics.median([r.get("num_comments") or 0 for r in rs])
    fl = sum(bool(r.get("link_flair_text")) for r in rs) / n
    lag = statistics.median([r["retrieved_on"] - r["created_utc"] for r in rs if r.get("retrieved_on")] or [0])
    zero = 31 - len(days)
    print(f"{sub:18s}{n:6d}{n/31:6.1f}{len(auth):6d}{100*top5:6.0f}{100*gh:5.1f}{100*tag:5.1f}"
          f"{100*rem:5.0f}{100*se:11.0f}{100*s1:10.0f}{mc:7.0f}{100*fl:7.0f}{lag:8.0f}{zero:9d}")
    for t in text:
        for m in TAG.findall(t):
            alltags[(sub, m.upper())] += 1
        for o, rp in GH.findall(t):
            allrepos[(o + "/" + rp).lower().rstrip(".git")] += 1
    for r in rs:
        hours[dt.datetime.utcfromtimestamp(r["created_utc"]).hour] += 1
    tot["posts"] += n
print("total posts", tot["posts"])
print("top cashtags (sub,tag):", alltags.most_common(15))
print("top repos:", allrepos.most_common(10))
print("unique repos linked:", len(allrepos), "total repo links:", sum(allrepos.values()))
print("hour-of-day UTC share:", {h: round(100 * c / tot["posts"], 1) for h, c in sorted(hours.items())})
