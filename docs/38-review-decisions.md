# 38 - Plan review decisions (facilitator)

Written October 14, 2026 after four independent reviews (planning docs, data model and labels, statistics, code). This file is the single source of truth for the cleanup. Where an older doc disagrees, this file wins until the doc is updated. Items marked **PARAMETER** are defaults the user may change. Items marked **USER** need a spending or risk decision from Eli.

## A. Claim, estimand and test

**D1. Primary claim is expected net abnormal return, not precision.**
- Estimand: mean net abnormal return (10 trading days, after an assumed round-trip cost, **PARAMETER** 20 bps) of flagged ticker-days minus the mean for matched control ticker-days.
- Test: one-sided, two-way clustered (D4) bootstrap lower bound of that difference is above zero.
- Hit rate and precision stay as descriptive outputs. The old hurdle H = 0.70 is retired as a pass/fail bar.
- Live threshold: break-even precision `p_be = (−E[R|miss]) / (E[R|hit] − E[R|miss])` estimated on training data (net of cost). Margin = lower bound of live `p` minus `p_be`. This keeps the ACT/WATCH/SKIP margin idea with a data-derived threshold.
- Why: a 0.70 precision bar is not a profit claim (small capped wins, fat-tailed losses), and the old power simulation tested a different question (flagged vs 5% base) than the registered test.

**D2. Unit and decision time.**
- Unit: ticker-day (ticker, UTC date). Cluster key: ticker.
- Decision time: 00:00 UTC of the next day (end of the UTC day). Features use only posts with timestamp at or before decision time. Entry is the first close strictly after decision time (DST-aware close, `labels.close_utc`).
- Cost: day-of reaction is excluded. This is conservative and removes within-day look-ahead. An intraday variant is a later extension, not a default.

**D3. Single primary window.**
- Primary: 10 trading days. Robustness (pre-registered, reported, not selected on): 5 and 21. The voter ensemble in `17` is used only for exploratory weighting, never for the confirmatory verdict.
- Benchmark: market plus sector ETF with beta fixed at 1 for the exploratory pass. A fitted market model is a pre-registered robustness check.

**D4. Null and clustering.**
- Matched controls: same ticker, within the surrounding 8 weeks, non-flagged days, matched on trailing 5-day and 21-day return, volume ratio, trailing volatility and prior mention count. Non-overlapping 10-day windows only.
- Clustering: two-way (ticker and calendar week) or a calendar-week block bootstrap. Ticker-only clustering is not accepted.
- Momentum control: a pre-entry abnormal-return band is a hard eligibility gate (**PARAMETER**: trailing 5-day abnormal return within ±2 trailing standard deviations), and CAR is scaled by trailing volatility for the secondary analysis.

**D5. Splits and leakage.**
- Report a purged forward-only fold (20-day purge and 20-day embargo, nothing after the test block in training) next to the interior sealed blocks in `32`.
- Report 5-fold ticker-grouped cross-validation to show same-ticker leakage.
- Validation block used to fix the flag cutoff is disjoint from sealed blocks and their embargoes.

**D6. Trial counter.** Every window, threshold, benchmark, sub subset, model variant, flag cutoff and era split is a trial. The confirmatory phase pre-specifies a ladder of at most 20 specifications and uses Holm correction over it. `T_eff` is not estimated post hoc.

**D7. Sample-size gates are defined without outcomes.** `n_flag` is computed from scores before any price join. The extension rule is fixed in advance and applies once.

**D8. Power simulation targets the real estimand.** Net-return lower bound with two-way clustering, a date-level shock, overlapping windows, flag clustering, a regime break, flag rate 0.5% base case (sensitivity 0.1% to 2%), at least 2,000 null simulations. Output is "units needed for 80% power" per true net edge in basis points. The old table in `31` is kept as the "flag vs base rate" detection check and labelled as such.

## B. Data validity

**D9. Point-in-time rule.** Every variable in `19` carries `known_at` (T, T+lag, or label-side) and a feature enters only if `known_at <= decision time`. `Item.feature_view()` is an explicit allowlist.
- Excluded from stage 1 (audit fields only): `removed_flag`, `removed_by_category`, `removed_frac`, `edited`, `link_flair_text`, `subreddit_subscribers`, all score and comment-count fields, `author` karma.
- Posts with `edited` set are dropped from training and flagged live (text may include later outcomes).
- Flair returns only after a per-sub point-in-time check. Removed status is tracked as a covariate for selection-bias reporting, not a feature.

**D10. Entity and price coverage.**
- The SEC ticker table is a current snapshot. Accepted for the exploratory pass. Report resolved share and unobservable share by year, and by sub.
- A price series is valid for a mention only if its first date is at or before the mention date (entry gap cap 5 calendar days, implemented).
- Unobservable rows are never silently dropped from the headline: the report bounds precision and mean return by worst-case imputation (unobservable as miss, then as hit) and lists the unobservable share per year.
- **USER:** a cheap paid dataset with delisted names is required before the confirmatory phase. Not yet priced.

**D11. Removed bodies.** Hit rate and mean return are reported by removed status. Models are fit with and without removed-body rows.

## C. Live input contract (Eli's requirement)

**D12. New posts are converted to the exact training format before the model sees them.**
- One code path: raw record -> `to_item(transform_version)` -> resolver -> ticker-day aggregation (same function) -> feature spec -> frozen model.
- A frozen **feature spec** (ordered column names, dtypes, encodings, missing-value rules, `transform_version`, resolver and ticker-table version) is stored with the model and hashed. The scorer refuses to run on a spec-hash mismatch.
- Parity test: the same raw posts through the census path and through a live-collector-shaped path must give identical vectors. Run in CI and before every weekly report.
- Live-only caveats are documented, not hidden: capture lag (about 21 s), bodies already removed at capture, and decision time (D2).
- Drift monitor: population stability index per feature and sub mix against the training distribution, reported with each live report.

## D. Hygiene

**D13. Privacy.** `DUND_SALT` is required for any real run; no fallback constant. Raw author names and `author_fullname` are confined to the raw census files outside Dropbox and never appear in derived tables, QA output or reports.

**D14. Document policy.** Nothing is deleted. Superseded docs get a top banner: "SUPERSEDED by `07` and `38` (October 14, 2026)". Every doc starts with a Status line (Current, Exploratory, Superseded). No renumbering. The reading order is `07, 38, 24, 32, 28, 31, 25, 27, 37`.

**D15. Census.** The API's `after` is exclusive, so the pager steps back one second and dedupes by id, and fails loudly on a page of 100 posts in one second. The census QA script compares each month's count with an independent count on a sample of days.

## E. Parked

- GitHub-star and repo outcomes (`30`), VIC, comment pulls (comment-introduced tickers kept as a later event type, `28`), BigQuery, X, paid price data (D10).
