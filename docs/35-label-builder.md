# 35. Label builder

Code: `src/dund/labels.py`. Tests: `tests/test_labels.py` (23, synthetic prices). Pure stdlib. Implements the hit rule of `32` section 5 (D3, D4, D9) without reading any real price.

## Input

One gzipped CSV per ticker: `date,open,high,low,close,adj_close,volume`. `load_prices(path)` -> `PriceSeries`. Rows with blank or non-positive close/adj_close are dropped (a missing price, not a zero). Trading days are the dates present in the series.

## Definitions

- **Entry.** `entry_index(series, ts)`: the first trading day whose close, fixed at 21:00 UTC, is strictly after `ts`. Intraday posts (before 21:00 UTC) enter at that day's close; posts at or after 21:00 UTC, on weekends or on holidays enter at the next trading day's close. Naive datetimes are read as UTC. Entry price is that day's `close`; returns use `adj_close`.
- **Forward return.** `adj_close[entry+n] / adj_close[entry] - 1`, n in {1, 5, 10, 21, 63} trading days (series rows).
- **Benchmark.** Equal-weight mean of the supplied benchmark series' returns over the same dates: `{"market": SPY}` or `{"market": SPY, "sector": ETF}`. CAR = raw minus benchmark. Simplification: beta fixed at 1 (the prereg market model with betas on d-250..d-30 is not implemented here; flagged as a deviation to resolve before freeze).
- **Placebo.** Same ticker, n-day CARs whose entry index j is in `[entry-252, entry-1]` and exit index `j+n <= entry-1`, so every price is a close at or before `ts`. Windows that start on or contain a supplied event date are skipped. `placebo_percentile` = share of placebo CARs <= observed CAR; `placebo_p95` = nearest-rank 95th. Placebo windows overlap (not independent). Minimum 100 windows (`min_placebo`), else unscored.
- **Liquidity (D9).** Entry close >= $1; mean of close*volume over the 20 days strictly before the entry day >= $500,000 (fewer than 20 days of history counts as illiquid); market cap >= $50M if supplied, else `market_cap_unknown=True` and no exclusion.
- **Hit.** `hit_label(lab, window=10, car_floor=0.03, placebo_q=0.95, require_liquid=True)` -> `(label, reason)`; hit = CAR >= floor and placebo_percentile > q.

## Never-False rule

`None` (with reason), not `False`, for: `missing_price:no_series`, `missing_price:no_entry_after_ts`, `delisted_or_series_ended` (ticker series ends before the benchmark does), `insufficient_forward_window` (all data ends), `missing_benchmark`, `insufficient_placebo`, `illiquid:<price|adv|adv_insufficient_history|market_cap>`, `window_not_computed`. `False` means CAR was measured and missed.

## Functions

`load_prices`, `series_from_rows`, `entry_index`, `placebo_cars`, `label_event(ticker, ts, series, benchmarks, windows, event_dates, market_cap, min_placebo, lookback, price_floor, adv_floor, mcap_floor) -> EventLabel`, `hit_label`. Per-window output: `car`, `raw_return`, `benchmark_return`, `placebo_percentile`, `placebo_p95`, `n_placebo`, `reason`.

## Known gaps

- Prereg entry is "next-day open after close of d" (`32`); this builder uses the first close after `ts` as instructed, a more conservative-or-different timing to reconcile.
- Lead rule (criterion 3, prior 5-day abnormal return) is not implemented; compute with `placebo_cars`-style window ending at entry-1.
- Fixed 21:00 UTC ignores the EDT close (20:00 UTC); a post 20:00-21:00 UTC in summer is treated as pre-close.
- Splits/dividends rely on `adj_close`; the ADV floor uses unadjusted close.

## Update (facilitator, October 14, 2026)

The fixed 21:00 UTC close listed under deviations was a look-ahead bug in summer: a post at 20:30 UTC (16:30 EDT) would have entered at a close that had already printed. `close_utc()` now uses 20:00 UTC during US daylight time (2nd Sunday of March to 1st Sunday of November) and 21:00 otherwise. Three tests added (`DstCloseTest`). Remaining deviations: beta fixed at 1, lead rule not implemented, entry is the first close after T.
