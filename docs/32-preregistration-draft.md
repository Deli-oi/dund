# 32 - Pre-registration draft (confirmatory phase), version 2

> **Defaults adopted (October 14, 2026):** the open choices listed below were set by the facilitator at Eli's request. See `docs/38-review-decisions.md` section F. They freeze with this document.

Status: Current, DRAFT, not frozen. Version 2, October 14, 2026. Built on `38` (authoritative decisions D1 to D11, D13), `24` (frame), `23` (data need), `16` and `17` (labels, weights), `28` (ticker-day unit, levers), `25` (the 14 subs), `31` (power simulation). Freeze rule: this file is hashed and dated, with `label_version`, `data_snapshot_id` and code commit recorded in section 14, **before any outcome (price) data is joined to the sealed period**. No results exist yet. Every number marked "planning" is arithmetic under assumptions, not a measurement. Paper only, not investment advice.

Items marked **DECISION NEEDED** are Eli's calls, with a recommended default that applies if no answer is given before freezing. Items now settled say "decided in 38". The consolidated list is in section 15.

## Changelog: v1 to v2

Four independent reviews (planning docs, data model and labels, statistics, code) found problems in v1. What changed and why:

| Review finding | v1 | v2 |
|---|---|---|
| Estimand mismatch | Primary test was precision above H = 0.70; the old power simulation tested flagged versus a 5% base rate, a different question. A 0.70 precision bar is not a profit claim (small capped wins, fat-tailed losses). | Primary estimand is the net abnormal-return difference versus matched controls; precision and hit rate are descriptive; live threshold is break-even precision (sections 5 to 8). H = 0.70 is retired as a pass/fail bar (the former section 8 is reworded in section 8). |
| Null and clustering | Placebo null on random non-post dates; ticker-only clustering; overlapping windows. | Matched-control null (same ticker, 8 weeks, matched covariates), non-overlapping windows, two-way (ticker and calendar week) clustered bootstrap, hard momentum gate (section 6, 7). |
| Multiple testing | Trial count `T_eff` estimated post hoc with a Bonferroni-style penalty; several windows and benchmarks implicit. | Pre-specified ladder of at most 20 specifications, Holm correction; single primary window with 5 and 21 as robustness (sections 5, 7). |
| Leakage | Interior blocks only, same-ticker leakage unmeasured, flag cutoff validation not disjoint, features included score and removal fields, decision time ambiguous, price coverage silently dropped. | Purged forward-only fold plus ticker-grouped CV, disjoint validation block, point-in-time allowlist, decision time 00:00 UTC next day, entity and price coverage with worst-case bounds, removed-body reporting (sections 2, 4, 10 to 12). |
| Sample-size gates | `n_flag` defined partly on outcomes via unknown rows; extension rule loose. | `n_flag` computed from scores before any price join; one fixed extension (section 9). |

Reworded rather than deleted: sections 1, 5, 6, 7, 8, 9 and 10 replace v1 text on H = 0.70, placebo-95th-percentile hit rule, ticker-clustered precision test and precision verdict table. The v1 hit definition survives as a descriptive hit rule (section 5). Exclusions and liquidity floors (section 12) are kept.

## 1. Hypothesis (from `24`)

H1: a signal set `S`, computed from posts in source universe `U`, produces an early call `C` whose flagged ticker-days earn a higher mean net abnormal return (10 trading days, after an assumed round-trip cost) than matched control ticker-days, with a one-sided two-way clustered bootstrap lower bound of the difference above zero, out of time (decided in 38, D1).

H0: the mean net abnormal-return difference of flagged versus matched control ticker-days is at or below zero.

Precision and hit rate are reported descriptively and compared with the break-even precision. The former hurdle H = 0.70 is not a bar (decided in 38, D1).

## 2. Unit of analysis and decision time

- **Unit: the ticker-day** (ticker, UTC date) (decided in 38, D2). One row per ticker and UTC date aggregating all in-universe posts naming the ticker. Per `28`, posts on the same ticker-day move together, so the post is not the independent unit.
- **Decision time: 00:00 UTC of the next day.** Features use only posts with timestamp at or before decision time. **Entry** is the first close strictly after decision time (DST-aware close, `labels.close_utc`). Day-of reaction is excluded (conservative, no within-day look-ahead). An intraday variant is a later extension, not part of this test.
- **Clustering:** two-way, ticker and calendar week (section 7). Report number of tickers, ticker-days, calendar weeks and `N_eff` as in `17`.
- Multi-entity posts contribute one mention to each named ticker.
- **Weights:** the confirmatory test is unweighted by `w`. `w` from `17` is a training device and must not enter the test.

## 3. Source universe U

Posts (submissions only) from these 14 subreddits (`25`): wallstreetbets, LocalLLaMA, coolgithubprojects, ValueInvesting, mcp, biotech, investing, MachineLearning, pennystocks, algotrading, AMD_Stock, smallcapstocks, OpenWebUI, SecurityAnalysis.

Source: Arctic Shift posts export. Only rows that name a US-listed equity ticker enter the market test. Comments, tokens, repo-only posts and other sources (`26`, `27`) are out of U for the confirmatory test.

**DECISION NEEDED (U): universe breadth.** Default: all 14. Alternative: the six cashtag-heavy subs (wallstreetbets, pennystocks, ValueInvesting, investing, smallcapstocks, AMD_Stock), more efficient but a narrower claim. (Not covered by `38`; remains Eli's.)

Ticker detection: cashtag (`$ABC`) only, regex frozen in the code commit. Name-only mentions are excluded. The SEC ticker table is a current snapshot; accepted for the exploratory pass; a paid dataset with delisted names is required before the confirmatory phase (`38` D10, USER item, not yet priced).

## 4. Signal definition S and point-in-time rules

`S` is a fixed, versioned feature vector per ticker-day.

- **Point-in-time rule (decided in 38, D9).** Every variable in `19` carries `known_at` (T, T+lag, or label-side). A feature enters only if `known_at <= decision time`. `Item.feature_view()` is an explicit allowlist.
- **Excluded from stage 1** (audit fields only): `removed_flag`, `removed_by_category`, `removed_frac`, `edited`, `link_flair_text`, `subreddit_subscribers`, all score and comment-count fields, author karma.
- Posts with `edited` set are dropped from training and flagged live. Flair returns only after a per-sub point-in-time check. Removed status is a covariate for selection-bias reporting, not a feature.
- Allowed: mention count, distinct authors, subreddit mix, first-mention-in-window flag (`16`), text-derived features at a named version from `19`, and trailing price features through decision time (asset-only baseline). Nothing uses price or volume after decision time.
- The variable list, transforms and model class are in the frozen code commit. One code path from raw record to frozen model, with a hashed feature spec (`38` D12).

**DECISION NEEDED (model class): D2 in v1.** Default: regularized logistic model on ticker-days (continuous outcome as secondary), trained only on non-sealed periods. (Remains Eli's, not in `38`.)

## 5. Early-call rule C, window and outcome

**Call C.** The model outputs a calibrated probability `p̂`. C fires when `p̂` is at or above a cutoff fixed on the validation block only (disjoint from sealed blocks and their embargoes, `38` D5) and frozen. `n_flag` is computed from scores before any price join (section 9). At most one flag per ticker per 10 trading days counts (non-overlapping windows, D4).

**Primary window (decided in 38, D3).** 10 trading days from entry. Robustness windows 5 and 21 days are pre-registered, reported, and not selected on. The voter ensemble in `17` is exploratory weighting only and never used for the confirmatory verdict.

**Benchmark (decided in 38, D3).** Market plus sector ETF with beta fixed at 1 for the primary pass. A fitted market model (betas on days `d-250` to `d-30`) is a pre-registered robustness check. Sector ETF map frozen at snapshot.

**Outcome.** Net abnormal return = cumulative abnormal return over the window minus the round-trip cost.

**DECISION NEEDED (cost): round-trip cost assumption.** Parameter default 20 bps (`38` D1). Eli confirms or changes before freezing; small caps may need more.

**Descriptive hit.** A flagged ticker-day is a hit if net abnormal return > 0. The v1 rule (CAR at least +3% and above placebo 95th percentile) is kept as a secondary descriptive hit definition. Unobservable rows are never dropped silently (section 11).

**Break-even precision (decided in 38, D1).** `p_be = (-E[R|miss]) / (E[R|hit] - E[R|miss])` estimated on training data net of cost. Live margin = lower bound of live precision minus `p_be`. This keeps the ACT/WATCH/SKIP margin idea with a data-derived threshold.

**Confounders.** Rows with a dated catalyst the post did not name (earnings, M&A, FDA) in the window are excluded and counted (`17`). Calendar source frozen in the commit.

## 6. The null: matched controls and momentum gate

- **Matched controls (decided in 38, D4).** For each flagged ticker-day, controls are non-flagged days of the same ticker within the surrounding 8 weeks, matched on trailing 5-day return, trailing 21-day return, volume ratio, trailing volatility and prior mention count. Only non-overlapping 10-day windows enter, both for flags and controls.
- **Momentum gate.** A pre-entry abnormal-return band is a hard eligibility gate: trailing 5-day abnormal return within a band of trailing standard deviations. CAR is scaled by trailing volatility for the secondary analysis.

**DECISION NEEDED (momentum band).** Parameter default ±2 trailing standard deviations (`38` D4). Eli confirms or sets the band before freezing.

- Control-set size, caliper and the matching fraction achieved are recorded before unsealing. Flags without an adequate control are counted and reported.

## 7. Primary test and multiplicity

- **Estimand (decided in 38, D1, D4).** `Δ` = mean net abnormal return of flagged ticker-days minus mean for matched control ticker-days, 10 trading days, after cost.
- **Test.** One-sided, alpha 0.05. Two-way clustered bootstrap (ticker and calendar week, 10,000 resamples; or a calendar-week block bootstrap) lower bound of `Δ` above zero. Ticker-only clustering is not accepted.
- **Ladder and Holm (decided in 38, D6).** Every window, threshold, benchmark, sub subset, model variant, flag cutoff and era split is a trial. The confirmatory phase pre-specifies a ladder of at most 20 specifications and applies Holm correction over it. `T_eff` is not estimated post hoc. The primary test is the first rung (10-day, market plus sector ETF, frozen cutoff, pooled sealed set).

**DECISION NEEDED (ladder): the 20 specifications.** Eli and the analysis lead list the at most 20 rungs (windows 5, 10 and 21; benchmark variants; cutoff variants; sub subsets; with and without removed bodies; era splits) before freezing. No default beyond the three windows and the fitted-beta check.

- **Baselines.** The flagged set is compared with each baseline (asset's own trailing return, repo-only features if applicable, base rate of unflagged ticker-days) by paired difference with the same bootstrap.
- **Descriptive outputs (not tests).** Precision, hit rate, break-even margin, by sub, era, block and removed status.

## 8. Retirement of H = 0.70

The v1 requirement `LB_95(precision) > 0.70` is retired as a pass/fail bar (decided in 38, D1). Reason: a 0.70 precision bar is not a profit claim. The role of "a margin above break-even" is kept: the live margin is the lower bound of live precision minus the data-derived `p_be` (section 5). A point estimate or lower bound of precision is reported next to `p_be` in every report.

## 9. Sample-size gates, power plan and extension

- **`n_flag` is computed outcome-free (decided in 38, D7):** from scores and the frozen cutoff, before any price join.
- **Power plan (decided in 38, D8).** The v2 simulation in `31` targets the real estimand: net-return lower bound with two-way clustering, date-level shock, overlapping windows, flag clustering, a regime break, flag rate 0.5% base case (sensitivity 0.1% to 2%), at least 2,000 null simulations. Output: units needed for 80% power per true net edge in basis points. Numbers: **to be filled by the power simulation v2.** The old `31` table is the "flag vs base rate" detection check only.
- **Minimum flagged units for any verdict other than Underpowered:** to be filled by the power simulation v2 (v1 value 100 flags from 40 tickers is a placeholder, not a result).
- **Pre-unseal check:** uses only validation-period flag rate and cluster measures. If projected sealed `n_flag` is below the minimum, the test is not run and the verdict is Underpowered by rule.
- **Stopping and extension (decided in 38, D7).** The sealed test is evaluated once. No interim looks at outcomes. If `n_flag` is below the minimum, the sealed data is extended once by the next calendar block in section 11 (fixed in advance, applies once), then evaluated once. Still below: Underpowered, study stops.

## 10. Verdicts and decision table

Evaluated on the sealed set after exclusions, using `Δ`, its lower bound `LB` and upper bound `UB` (one-sided 95%), and Holm-adjusted p over the ladder.

| Verdict | Criteria (all must hold) |
|---|---|
| **Supported** | (a) `n_flag` at or above the minimum from `31` v2 and distinct tickers at or above its ticker minimum; (b) `LB(Δ) > 0` for the primary rung, and Holm-adjusted over the ladder; (c) paired lower bound of the difference versus every baseline > 0; (d) the worst-case unobservable bound (section 11) keeps `LB(Δ) > 0` when unobservable rows are imputed as misses; (e) the 5-day and 21-day robustness windows have point estimates of the same sign and are not contradicted; (f) each of the two sealed eras has a point estimate of `Δ` above zero; (g) the purged forward-only fold (`38` D5) agrees in sign. Until replication on later live data does not contradict, the label is "Supported, pending replication". |
| **Not supported** | `n_flag` at or above the minimum and `UB(Δ) < 0`, or `UB(Δ)` is below the smallest edge of interest (**DECISION NEEDED** below), or a baseline is beaten the other way on a tight interval. |
| **Underpowered** | Anything else: `n_flag` below the minimum or too few tickers; or `LB(Δ) ≤ 0 ≤ UB(Δ)`; or the interval is wider than the width set by the power plan at the end of the extension. Reported as "could not tell", never as a pass. |

Edge cases: if (b) holds but (d), (e), (f) or (g) fails, the verdict is Underpowered with the failing condition named, unless that quantity has a tight interval on the wrong side, in which case Not supported. The paper-style output is the same for all three (`24`).

**DECISION NEEDED (minimum edge of interest).** The smallest net edge (bps) that would be worth acting on, used to define "tight" for Not supported. Suggested: fill from the power simulation v2 output once available.

## 11. Entity and price coverage, bounds, removed bodies

- **Coverage (decided in 38, D10).** Report resolved share and unobservable share by year and by sub. A price series is valid for a mention only if its first date is at or before the mention date (entry gap cap 5 calendar days).
- **Bounds.** Unobservable rows are never silently dropped from the headline. Mean return and precision are bounded by worst-case imputation: unobservable as miss, then as hit.
- **Removed bodies (decided in 38, D11).** Hit rate and mean return by removed status. Models are fit with and without removed-body rows. Removal remains a covariate for selection-bias reporting, not a feature.

## 12. Sealed test period and exclusions

### Sealed periods

Two disjoint blocks, one per era, because WSB behavior has a regime break at January 2021 (`15`, `17`).

| Block | Dates (inclusive) | Era | Why |
|---|---|---|---|
| A | 2020-01-01 to 2020-12-31 | Pre-2021 | Full year before the break, includes COVID volatility |
| B | 2021-07-01 to 2022-06-30 | Post-January-2021 | After the meme peak, measures the post-break regime; includes a falling market |
| Extension (once, section 9) | 2023-01-01 to 2023-12-31 | Post | Used only if `n_flag` is below the minimum |

- **Purge and embargo (decided in 38, D5).** 20-day purge and 20-day embargo on each side of each block. In addition, a **purged forward-only fold** (nothing after the test block in training) is reported next to the interior blocks, and **5-fold ticker-grouped cross-validation** is reported to show same-ticker leakage. The validation block used to fix the flag cutoff is disjoint from sealed blocks and their embargoes.
- **Time order.** Interior blocks weaken the out-of-time claim; the forward-only fold and replication on live data address this.
- January to June 2021 stays outside the sealed set (meme dominance, `28`). Prices for dates inside the blocks are not joined before freeze.

**DECISION NEEDED (sealed dates).** Default: blocks A and B above, extension 2023. Alternatives: include 2021-01 to 2021-06 in block B; or put the sealed block at the latest data (2025 to 2026) for a single era and cleaner out-of-time claim. Remains Eli's.

### Exclusions (kept from v1)

Applied before unsealing, by frozen code; counts reported by reason.

| Exclusion | Rule |
|---|---|
| Single-letter tickers | Drop cashtags of length 1. Length-2 tickers pass only if on the listed-ticker file and not a common English word on a frozen list. |
| Removed or deleted bodies | `[removed]` or `[deleted]` bodies or author: title-only if a cashtag is in the title, otherwise excluded. Removed rate per sub and era (`25`: 7 to 47%). Reporting and with/without fits per section 11. |
| Liquidity floor | At decision time: close at or above $1.00, 20-day average dollar volume at or above $500,000, market cap at or above $50 million where available. |
| Missing price data | Fewer than 150 prior days or missing prices in the window (including delisting inside it): unscored, counted, and bounded per section 11. |
| Catalyst confounds | Per section 5. |
| Ticker cap | No single ticker above 2% of flagged units in the primary count (rest kept for sensitivity). |
| Non-US-listed or OTC-pink | Excluded. |
| Duplicates and bots | Cross-posts of the same text on the same day are one mention. Authors on the frozen bot list dropped. Raw author names never appear in derived tables (`38` D13). |

**DECISION NEEDED (liquidity floors).** Default: $1, $500k ADV, $50M cap. Alternative: $5 and $2M, which suits "tradable" better but removes most of pennystocks and smallcapstocks. Kept from v1.

## 13. What counts as a deviation

A **deviation** is any departure from this file after freezing, logged in section 14 with date, reason, and "before unsealing" or "after unsealing".

- **Major (invalidates the confirmatory label, result reported as exploratory):** any change to U, S, C, window, benchmark, cost, momentum band, ladder, matching rule, null, test, alpha, sealed dates, or exclusions after seeing any sealed outcome; re-running the sealed test with a changed spec; evaluating more than once; reading sealed outcomes before freeze.
- **Minor (allowed, logged):** bug fixes that do not change a definition and are found without looking at sealed outcomes; pull retries and API outages; a ticker-file update applied identically to all periods. One-line justification and a diff of counts.
- **Not a deviation:** additional descriptive analyses clearly marked exploratory.

If a major deviation occurs, the original pre-registered analysis is still run and reported next to the new one.

## 14. Freeze record (to complete at freezing)

| Field | Value |
|---|---|
| Date and time frozen | |
| File hash of this document | |
| Code commit | |
| `label_version` | |
| `data_snapshot_id` | |
| Feature spec hash and `transform_version` | |
| Ladder of at most 20 specifications | |
| Cost assumption (bps) and momentum band | |
| Validation flag rate, cluster measures, matching fraction | |
| Power simulation v2 output (`31`) | |
| Deviation log | |

## 15. DECISION NEEDED summary (Eli)

Decided in 38 and removed from this list: estimand and test (D1), unit and decision time (D2), window and benchmark (D3), null, clustering and momentum gate form (D4), splits (D5), trial ladder and Holm (D6), sample-size gates and extension (D7), power plan target (D8), point-in-time rules (D9), coverage and bounds (D10), removed bodies (D11).

| # | Item | Recommended default |
|---|---|---|
| 1 | Round-trip cost assumption | 20 bps |
| 2 | Sealed dates | A: 2020; B: 2021-07 to 2022-06; extension 2023 |
| 3 | The ladder of at most 20 specifications | Three windows, fitted-beta check, cutoff and removed-body variants; to be listed |
| 4 | Momentum band | within ±2 trailing standard deviations |
| 5 | Universe breadth | All 14 subs |
| 6 | Model class | Regularized logistic on ticker-days |
| 7 | Liquidity floors | $1, $500k ADV, $50M cap |
| 8 | Minimum edge of interest (defines "tight") | From power simulation v2 |

Also open (USER, `38` D10): price and delisted-names dataset, not yet priced, required before the confirmatory phase.
