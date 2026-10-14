# 34 - Price pull (Yahoo chart API)

## How to run

```
python scripts/pull_prices.py tickers.txt C:\Users\dalele\dund-data\prices
```

- Input: text file, one ticker per line (`#` comments ok). `BRK.B` is normalized to `BRK-B`.
- Benchmarks always added: SPY, XLK XLF XLV XLE XLY XLP XLI XLB XLU XLRE XLC, ^GSPC (stored as `_GSPC.csv.gz`). `--no-benchmarks` skips them. FRED SP500 covers only ~10 years, so Yahoo is the main benchmark source.
- Output: `{TICKER}.csv.gz` (date, open, high, low, close, adjclose, volume, dividend, split), `manifest.tsv` (ticker, first_date, last_date, rows), `misses.tsv` (ticker, http_status, reason).
- Resumable: tickers already in manifest or misses are skipped; rerun to continue. To retry misses, remove their lines.
- Safety: 1 request/s, exponential backoff on 429/5xx (5 tries), stops if C: free < 0.6 GB, writes via `.tmp` then rename. Start date default 2012-01-01 (`--start`).
- Tests: `pytest tests/test_pull_prices.py` (no network).

## Observed behavior (40-ticker test + 13 benchmarks, 2026-10-14)

- 53 requests in 53 s, no 429s. 44 ok, 9 misses. Output 3.2 MB.
- Live names (AAPL, GME, BRK-B, ^GSPC, etc.) full history from 2012-01-03 (3717 rows). AMC from 2013-12-18, CVNA from 2017-04-28.
- All misses were 404 "No data found, symbol may be delisted": SIVB, TWTR, FRC, SPLK, ATVI, CTXS, WORK (known delisted) plus WISH, EXPR.
- Caveat, survivorship: BBBY returned only 62 rows (2026-07-17 onward) and HTZ only from 2021-07, so a ticker being present does not mean pre-delisting history exists. Check `first_date` in the manifest before trusting a series; reused tickers are a silent trap.

## Terms of use / risk

Doc 29 notes that Yahoo's terms restrict automated and commercial use, and this is an unofficial API. This script does automated bulk downloading, which that restriction covers. The user accepted this risk for exploratory, personal, non-commercial use only. Do not redistribute the data or use it commercially; expect possible blocking. The plan is to replace it with a cheap paid historical dataset that includes delisted names.
