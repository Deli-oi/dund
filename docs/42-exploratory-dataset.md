# 42. Exploratory dataset

Status: Current. Code: `src/dund/sealed.py`, `scripts/build_exploratory.py`.

## What it is
One row per NON-sealed ticker-day with entry date, 5/10/21-day abnormal returns versus SPY (beta fixed 1; no sector map yet, market only), 10-day return net of 20 bps, placebo percentile, hit flag and the reason when the label is None. Plus `coverage.md`: per year and per sub, share with a price series, share None by reason, liquidity-flagged share, unobservable share, and hit-rate bounds (unobservable as miss, as hit). None is never a miss; the headline hit rate uses observable rows only.

## How sealing works
Blocks (docs/32): A = 2020; B = 2021-07-01 to 2022-06-30; extension = 2023. Purge before and embargo after: 30 calendar days each (conservative for 20 trading days). An event is sealed if its decision day, any day of its forward window (21 trading days converted to calendar days plus slack), or the purge zone touches a block. The builder skips sealed ticker-days before reading any price and only counts them. `label_event_guarded` raises `SealedAccessError` unless `unseal_token='I-ACCEPT-ONE-TIME-UNSEAL'`, a reason and an audit log path are given; each unseal appends a line to the log. An unseal is a major deviation (docs/32 section 13).

## How to run
`python -I scripts/build_exploratory.py TICKER_DAYS.csv.gz PRICES_DIR OUT_DIR` (PRICES_DIR holds `<TICKER>.csv.gz` and `SPY.csv.gz` from `pull_prices.py`). Stdout shows counts only.

## Allowed / not allowed
Allowed: coverage tables, descriptive hit rates and returns on the non-sealed output, feature exploration, model development on non-sealed rows.
Not allowed: pricing or inspecting sealed-period rows, running the builder with sealed dates patched out, tuning anything on sealed outcomes, printing per-ticker outcomes for sealed zones. Note that this dataset is exploratory and does not constitute the confirmatory test.
