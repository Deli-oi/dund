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

## F. Defaults adopted for the open pre-registration choices (October 14, 2026, delegated by Eli)

Eli asked the facilitator to choose the defaults and to expand the data supply (more subreddits) as needed. These are defaults, not frozen values. They freeze with `32` before any outcome data is joined.

| # | Choice | Default | Reason |
|---|---|---|---|
| 1 | Round-trip cost | 20 bps | Conservative for liquid US equities with the liquidity floors, and easy to stress at 50 bps as a sensitivity |
| 2 | Minimum edge of interest | **200 bps** net per flagged ticker-day over 10 days for the confirmatory claim (100 bps reported as an exploratory stretch) | Revised after power simulation v2 (`31`): 100 bps needs about 2,600 flagged units, which is not reachable. 200 bps needs about 640 |
| 3 | Confirmatory family | 3 tests: windows 5, 10 and 21 days, one benchmark (market plus sector), Holm over the 3 | A small family keeps power. Everything else is descriptive and labelled exploratory |
| 4 | Momentum gate | Trailing 5-day abnormal return within +/- 2 trailing standard deviations | As in D4 |
| 5 | Universe | The 14 census subs plus the expansion list approved before freeze (`40`), frozen as a list | More ticker-days. The list is fixed before outcomes are joined, so adding subs is not a trial |
| 6 | Model class | Regularized logistic regression on post-only features, ticker-day aggregated | Matches the project goal. Other models are exploratory |
| 7 | Liquidity floors | Price at least $1, average daily dollar volume at least $500k, market cap at least $50M | As in v1 of the draft. A $2 or $5 floor is a sensitivity |
| 8 | Sealed periods | As in `32` v2 (2020 and 2021-07 to 2022-06, extension 2023), revisit only if the census shows a block is too thin | Keeps both regimes represented |

### What "minimum edge" means, in plain terms

It is the smallest average gain per flagged call, after costs, that we would care to detect. If the real effect is smaller than that, we accept that we cannot tell it from zero. A smaller target needs much more data.

Back-of-envelope with 10-day abnormal return noise of about 8% to 10% (standard deviation), one-sided test at 5%, 80% power, independent flagged units, `n = (1.645 + 0.84)^2 x sd^2 / edge^2`:

| Edge worth detecting | Flagged units needed | Ticker-days at 2% flag rate | At 0.5% flag rate |
|---|---|---|---|
| 200 bps | about 125 | about 6,000 | about 25,000 |
| 100 bps | about 500 | about 25,000 | about 100,000 |
| 50 bps | about 2,000 | about 100,000 | about 400,000 |

These are rough and ignore clustering, which makes them worse. The power simulation v2 replaces them. At the 100 bps default, supply in `28` (8,000 to 34,000 ticker-days a year from 14 subs) is enough at a 2% flag rate over a few years and short at 0.5%, which is why more subs and more years matter.


### Correction after power simulation v2 (`31`)

The back-of-envelope table above ignored clustering, overlapping windows and the shared weekly shock, and it was far too optimistic. Simulated with a two-way clustered test, 0.5% flag rate, 80% power, 5% one-sided:

| True net edge | Flagged units needed | Ticker-days (0.5% flag rate) | Supply needed |
|---|---|---|---|
| 300 bps | about 280 | about 55,000 | about 1 to 3 years of expanded supply |
| 200 bps | about 640 | about 128,000 | about 3 to 8 years |
| 100 bps | about 2,600 | about 520,000 | about 10 to 26 years, not reachable |
| 50 bps | about 10,500 | about 2,100,000 | not reachable |

At a 2% flag rate the ticker-day counts are about 4 times smaller. The flag rate is an assumption until a model exists. A ticker-only clustered test has a 14% to 26% false-positive rate under the null, so the two-way test is required.

Reading: only an edge of about 200 bps or more is confirmable with this data. A smaller true edge would end as "Underpowered", which is a valid verdict under `32`, not a failure.

## G. Found in the first real data (October 14, 2026)

**D16. List posts and bots are not events.** The first exploratory run showed one subreddit (RobinHood, 2019) supplying 44% of all resolved ticker-days. The cause is a bot account posting a daily "Daily Stock Discussion Thread" whose body lists 50 to 150 tickers (one bot produced 2,705 candidates in a month). Such a post is an aggregate listing, is not a human early call, and may embed information gathered from later comments.
- A post that resolves to more than 10 distinct stock candidates is a **list post**: it creates no ticker-day events. It is counted and reported per sub-year.
- An author with 10 or more list posts in a month, or a name matching known bot patterns, is flagged as a **bot author** and all their posts are excluded from events and counted.
- Both rules are applied identically in training and live. They are parameters of the transform and appear in the feature spec.
- All counts reported before this fix (ticker-days, hit rates, coverage) are superseded. Rebuild before reading any result.
