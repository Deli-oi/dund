"""Pull daily adjusted OHLCV from the Yahoo chart API, one gzipped CSV per ticker.

Usage: python scripts/pull_prices.py TICKERS.txt OUT_DIR [--start 2012-01-01]
See docs/34-price-pull.md. Unofficial API; exploratory use only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "dund-research/0.1 (personal non-commercial research; elijahdalelio@gmail.com)"
URL = ("https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1={p1}&period2={p2}"
       "&interval=1d&events=div%2Csplits")
BENCHMARKS = ["SPY", "XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU",
              "XLRE", "XLC", "^GSPC"]
MIN_FREE_GB = 0.6
MIN_INTERVAL = 1.0
COLS = ["date", "open", "high", "low", "close", "adjclose", "volume", "dividend", "split"]


def normalize_ticker(t: str) -> str:
    """BRK.B -> BRK-B; strip, uppercase. Index symbols keep leading ^."""
    return t.strip().upper().replace(".", "-")


def file_stem(t: str) -> str:
    return t.replace("^", "_")


def to_epoch(d: dt.date) -> int:
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())


def parse_chart(payload: dict) -> list[dict]:
    """Parse a Yahoo chart JSON dict into row dicts. Raises ValueError if no data."""
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise ValueError(str(chart["error"].get("description") or chart["error"]))
    res = (chart.get("result") or [None])[0]
    if not res or not res.get("timestamp"):
        raise ValueError("no data")
    ts = res["timestamp"]
    ind = res.get("indicators", {})
    q = (ind.get("quote") or [{}])[0]
    adj = ((ind.get("adjclose") or [{}])[0]).get("adjclose") or [None] * len(ts)
    events = res.get("events") or {}
    divs = {int(k): v.get("amount") for k, v in (events.get("dividends") or {}).items()}
    splits = {int(k): "%s:%s" % (v.get("numerator"), v.get("denominator"))
              for k, v in (events.get("splits") or {}).items()}

    def day(x):
        return dt.datetime.fromtimestamp(x, dt.timezone.utc).date().isoformat()

    divs = {day(k): v for k, v in divs.items()}
    splits = {day(k): v for k, v in splits.items()}
    rows = []
    for i, t in enumerate(ts):
        c = q.get("close", [None] * len(ts))[i]
        if c is None:
            continue
        d = day(t)
        rows.append({
            "date": d,
            "open": q["open"][i], "high": q["high"][i], "low": q["low"][i],
            "close": c, "adjclose": adj[i], "volume": q["volume"][i],
            "dividend": divs.get(d, ""), "split": splits.get(d, ""),
        })
    if not rows:
        raise ValueError("no data")
    return rows


def write_rows_atomic(path: Path, rows: list[dict]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with gzip.open(tmp, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in COLS})
    tmp.replace(path)


def append_atomic(path: Path, line: str) -> None:
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(line + "\n")


def load_done(out: Path) -> set[str]:
    """Tickers already finished: manifest or miss entries."""
    done = set()
    for name in ("manifest.tsv", "misses.tsv"):
        p = out / name
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines()[1:]:
                if line.strip():
                    done.add(line.split("\t")[0])
    return done


def fetch(ticker: str, p1: int, p2: int):
    """Return (status, payload_or_None, reason). Retries with backoff on 429/5xx."""
    url = URL.format(t=urllib.request.quote(ticker, safe="^-"), p1=p1, p2=p2)
    delay = 5.0
    for attempt in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8")), ""
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(delay)
                delay *= 2
                continue
            reason = ""
            try:
                body = json.loads(e.read().decode("utf-8"))
                reason = (body.get("chart", {}).get("error") or {}).get("description", "")
            except Exception:
                pass
            return e.code, None, reason or e.reason
        except Exception as e:  # network error
            time.sleep(delay)
            delay *= 2
            last = repr(e)
    return 0, None, "gave up after retries"


def run(tickers: list[str], out: Path, start: dt.date, free_path: str = "C:\\") -> int:
    out.mkdir(parents=True, exist_ok=True)
    mf, ms = out / "manifest.tsv", out / "misses.tsv"
    if not mf.exists():
        mf.write_text("ticker\tfirst_date\tlast_date\trows\n", encoding="utf-8")
    if not ms.exists():
        ms.write_text("ticker\thttp_status\treason\n", encoding="utf-8")
    done = load_done(out)
    p1, p2 = to_epoch(start), to_epoch(dt.date.today() + dt.timedelta(days=1))
    last = 0.0
    n_ok = n_miss = 0
    for t in tickers:
        if t in done:
            continue
        if shutil.disk_usage(free_path).free / 1e9 < MIN_FREE_GB:
            print("disk guard: stopping, free space below %.1f GB" % MIN_FREE_GB)
            break
        wait = MIN_INTERVAL - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.time()
        status, payload, reason = fetch(t, p1, p2)
        if payload is not None:
            try:
                rows = parse_chart(payload)
                write_rows_atomic(out / (file_stem(t) + ".csv.gz"), rows)
                append_atomic(mf, "%s\t%s\t%s\t%d" % (t, rows[0]["date"], rows[-1]["date"], len(rows)))
                n_ok += 1
                continue
            except ValueError as e:
                reason = str(e)
        append_atomic(ms, "%s\t%s\t%s" % (t, status, reason.replace("\t", " ").replace("\n", " ")))
        n_miss += 1
    print("ok=%d miss=%d" % (n_ok, n_miss))
    return 0


def read_tickers(path: Path) -> list[str]:
    seen, out = set(), []
    for line in path.read_text(encoding="utf-8").splitlines():
        t = normalize_ticker(line)
        if t and not t.startswith("#") and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers_file", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--start", default="2012-01-01")
    ap.add_argument("--no-benchmarks", action="store_true")
    a = ap.parse_args(argv)
    tickers = read_tickers(a.tickers_file)
    if not a.no_benchmarks:
        tickers = BENCHMARKS + [t for t in tickers if t not in BENCHMARKS]
    return run(tickers, a.out_dir, dt.date.fromisoformat(a.start))


if __name__ == "__main__":
    sys.exit(main())
