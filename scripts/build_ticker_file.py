"""Download SEC company_tickers.json and build a normalized tickers.csv.

Usage: python -I build_ticker_file.py OUT_DIR   (OUT_DIR must be new/empty or absent)
Output: OUT_DIR/company_tickers.json (raw), OUT_DIR/tickers.csv (ticker,title,cik)
"""
import csv
import json
import sys
import urllib.request
from pathlib import Path

URL = "https://www.sec.gov/files/company_tickers.json"
UA = "dund-research/0.1 elijahdalelio@gmail.com"


def main(out_dir: str) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        print("refusing: output directory not empty", file=sys.stderr)
        return 1
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    (out / "company_tickers.json").write_bytes(raw)
    data = json.loads(raw)
    rows, seen = [], set()
    for rec in data.values():
        t = str(rec.get("ticker", "")).strip().upper()
        title = " ".join(str(rec.get("title", "")).split())
        cik = str(rec.get("cik_str", "")).strip().zfill(10)
        if not t or not title or not cik.isdigit() or t in seen:
            continue
        seen.add(t)
        rows.append((t, title, cik))
    rows.sort()
    with open(out / "tickers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "title", "cik"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out / 'tickers.csv'}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_ticker_file.py OUT_DIR")
    sys.exit(main(sys.argv[1]))
