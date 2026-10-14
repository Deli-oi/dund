# 32 - Pre-registration draft (confirmatory phase)

October 14, 2026. DRAFT, not frozen. Built on `24` (frame), `23` (data need), `16` and `17` (labels, weights), `28` (ticker-day unit, levers), `25` (the 14 subs). Freeze rule: this file is hashed and dated, with `label_version`, `data_snapshot_id` and code commit recorded in section 14, **before any outcome (price) data is joined to the sealed period**. No results exist yet. Every number marked "planning" is arithmetic under assumptions, not a measurement. Paper only, not investment advice.

Items marked **DECISION NEEDED** are Eli's calls. Each has a recommended default that applies if no answer is given before freezing. A consolidated list is in section 15.

## 1. Hypothesis (from `24`)

H1: a signal set `S`, computed from posts in source universe `U`, produces an early call `C` whose hit rate, with its one-sided lower confidence bound at level `L = 95%`, exceeds the hurdle `H = 0.70` and beats the baselines, out of time and net of the cost floor in section 5.

H0: precision of flagged ticker-days is at or below `H`, or is not distinguishable from the placebo/baseline rate (section 6).

## 2. Unit of analysis

- **Unit: the ticker-day.** One row per (ticker, US trading day `d`), aggregating all in-universe posts that name the ticker between the close of `d-1` and the close of `d` (America/New_York). Per `28`, posts on the same ticker-day move together, so the post is not the independent unit.
- **Clustering: by ticker.** Same-ticker rows across days and months are correlated (`28`). All intervals and tests use ticker-clustered variance. Effective N reporting: number of tickers, number of ticker-days, and `N_eff` as in `17`.
- Multi-entity posts contribute one mention to each named ticker (resolves open item 1 in `16` for the confirmatory table; the exploratory table is unchanged).
- Weights: the confirmatory test is **unweighted by `w`** (no decay, no materiality, no negatives multiplier). `w` from `17` is a training device and must not enter the test.

## 3. Source universe U

Posts (submissions only, post level) from these 14 subreddits (`25`):

1. wallstreetbets
2. LocalLLaMA
3. coolgithubprojects
4. ValueInvesting
5. mcp
6. biotech
7. investing
8. MachineLearning
9. pennystocks
10. algotrading
11. AMD_Stock
12. smallcapstocks
13. OpenWebUI
14. SecurityAnalysis

Source: Arctic Shift posts export. Only rows that name a US-listed equity ticker enter the market test; the tech and repo subs contribute few such rows and are kept so the universe matches what was explored. Comments, tokens, repo-only posts and other sources (`26`, `27`) are **out of U** for the confirmatory test and belong to replication or follow-up.

**DECISION NEEDED (D1): universe breadth.** Default: all 14 as listed. Alternative: restrict to the six subs that carry most cashtags (wallstreetbets, pennystocks, ValueInvesting, investing, smallcapstocks, AMD_Stock), which is more efficient but narrows the claim.

Ticker detection: cashtag (`$ABC`) only, regex frozen in the code commit. Name-only mentions are excluded from the confirmatory test (not measured, unvalidated).

## 4. Signal definition S

`S` is a fixed, versioned feature vector per ticker-day, computed only from information time-stamped at or before the close of day `d`:

- mention count, distinct authors, subreddit mix, first-mention-in-window flag (`16`), post score and comment count at pull time excluded (look-ahead risk), text-derived features from the frozen list in the variable catalog (`19`) at a named version.
- No feature may use price or volume after the close of `d`. Trailing price features through `d` are allowed and form the asset-only baseline.

The exact variable list, transforms, and model class are written into the frozen code commit. Variables not in that list cannot be added after unsealing.

**DECISION NEEDED (D2): model class.** Default: a regularized logistic model on ticker-days (continuous outcome kept as a secondary check), trained only on non-sealed periods, with the exploratory trial count recorded.

## 5. Early-call rule C and hit definition

**Call C.** For ticker-day `d`, the model outputs a calibrated probability `p̂`. C fires ("flag") if the lower bound of its calibrated interval is at least `H = 0.70` (`18` margin rule). The cutoff is fixed on the training/validation periods only and is frozen. The flag rate is reported; at most one flag per ticker per 5 trading days counts (later flags inside that span are dropped, to keep hits from overlapping).

**Entry.** Next-day open after the close of `d` (the earliest realistic fill). Return window starts there.

**Hit (primary).** A flagged ticker-day is a hit if the cumulative abnormal return from next open through the close of trading day `d+10` satisfies all of:

1. CAR ≥ +3.0% (a cost-and-slippage floor, see below), and
2. CAR exceeds the 95th percentile of that ticker's placebo CARs over the same window length on random non-post dates (`17`, `13` K1), minimum 100 placebo windows, else row is unscored (excluded, counted), and
3. the post window precedes the move (lead rule, `16`): the abnormal return in the 5 trading days before `d` is below the placebo 95th percentile.

**Benchmark.** Market-model abnormal return versus SPY plus the sector ETF of the ticker, with betas estimated on days `d-250` to `d-30` (no overlap with the window). Sector ETF map frozen at snapshot.

**Misses and unknowns.** Miss: CAR inside the placebo band. Between bands: "unknown," excluded from the numerator and denominator but reported in a sensitivity analysis counting all unknowns as misses (the bound must also hold there, otherwise the verdict is downgraded, section 10).

**Confounders.** Rows with a dated catalyst the post did not name (earnings, M&A, FDA) in the window are excluded and counted (`17`). The calendar source is frozen in the commit.

**DECISION NEEDED (D3): window and threshold.** Default: 10-day window, +3.0% floor. Alternatives: 5 days with +2%, or 20 days with +5%. Short-first fits `17`; the floor should exceed round-trip cost plus slippage for small caps.

**DECISION NEEDED (D4): benchmark.** Default: market plus sector ETF (the default recorded in `17` open item 1). Alternative: single index, which is simpler but leaves sector beta in the hit.

## 6. The null and its derivation

Two nulls are tested, in order:

- **N1 (detection null, derived).** For flagged ticker-days, the hit probability if the flag carried no information is `p0`. It is estimated empirically, not assumed: draw placebo ticker-days matched on ticker, month, and trailing 5-day return, apply the same hit rule, and take the hit fraction. By construction of rule 2 it is near 5%, but `p0` is whatever the placebo says and is recorded with its cluster-bootstrap interval before unsealing. The same procedure on the baselines (asset's own trailing return, repo-only features if applicable, base rate of unflagged ticker-days) gives `p_b`. The reference rate is `p_ref = max(p0, p_b)`.
- **N2 (hurdle null).** Precision of flags is ≤ `H = 0.70`.

Why two: N1 shows there is a signal; N2 is the stated bar for an actionable call. The 0.70 hurdle is about 14 times a 5% base rate (`23`), so a pass on N2 implies a pass on N1, but N1 is reported so a failure can be read correctly ("no signal" versus "signal but weak").

## 7. Primary test

- **Statistic.** Precision `π̂` = hits / (hits + misses) among flagged ticker-days.
- **Test.** One-sided test of H0: `π ≤ 0.70` against `π > 0.70`.
- **Variance.** Cluster-robust by ticker. Default: ticker-level cluster bootstrap (10,000 resamples) for the one-sided 95% lower bound; sandwich (CR2-type) estimate reported alongside as a check. The bootstrap is primary.
- **Alpha.** 0.05, one-sided. Confidence level `L = 95%` for the lower bound.
- **Multiplicity.** One primary test (N2 on the pooled sealed set). N1, and all slices (by sub, era, block), are secondary and descriptive.
- **Search penalty (`24`, `12`).** The exploratory trial count `T` is recorded. The primary test is evaluated at alpha/`T_eff` only if the frozen spec was selected by best-of-search over `T` > 1 trials. Otherwise unadjusted.
- **Baselines.** The flagged set must also beat each baseline on a paired ticker-cluster comparison (lower bound of precision difference > 0).
- **Profit claim (`24`).** Reported separately: paper return net of cost floor, lower bound above 0, drawdown inside `10`. It is required for "Supported" (section 10).

**DECISION NEEDED (D5): alpha and search penalty.** Default: alpha 0.05 one-sided, with a Bonferroni-style `T_eff` penalty as above. Alternative: 0.025 for a stricter bar, or a deflated-significance method from `12`.

## 8. Hurdle H = 0.70 on the confidence level

H applies to the **lower bound** of the 95% one-sided interval on precision, not the point estimate: the claim passes only if `LB_95(π̂) > 0.70`. A point estimate of 0.80 with a lower bound of 0.66 is not a pass. 0.70 is the default from `24`, `07`, `10` (breakeven plus safety margin).

## 9. Sample-size rule and stopping rule

**Planning arithmetic (not results).** To detect a true precision of 0.80 against 0.70 at one-sided alpha 0.05 and 80% power needs about 120 independent flagged units; with a cluster inflation of about 1.3 (within the 1.0 to 1.6 range in `28`, to be re-measured), about 155 flagged ticker-days. If 2% of scored ticker-days are flagged (assumption, measured at validation), that means about 7,800 scored ticker-days in the sealed set. Against about 700 to 2,900 ticker-days a month (`28`), that is roughly 3 to 11 months of sealed data. A true precision of 0.75 needs about 450 units, so the plan reaches the strong-effect case and not weak effects (`23`).

**Sample-size rule.**
- Minimum flagged units to be eligible for any verdict other than Underpowered: **n_flag ≥ 100 flagged ticker-days from ≥ 40 distinct tickers.**
- Target: n_flag ≥ 155.
- Before unsealing, a pre-unseal power check uses only validation-period flag rate and cluster inflation (no sealed outcomes). If projected sealed n_flag < 100, the test is not run and the verdict is Underpowered by rule.

**Stopping rule.** The sealed test is evaluated **once**, at the end of the sealed periods in section 11, over all data in them. No interim looks at outcomes, no early stopping for success. If n_flag is below 100 at the end, the pre-registered action is to extend the sealed data by adding the next unused calendar block in section 11 (once only, listed there), then evaluate once. If still below 100, verdict is Underpowered and the study stops.

**DECISION NEEDED (D6): minimum n and extension.** Default: 100 flags from 40 tickers, one extension. Alternative: a hard stop at the initial period with no extension (stricter against optional stopping, higher risk of Underpowered).

## 10. Verdicts

Evaluated in order on the sealed set after applying exclusions.

| Verdict | Exact criteria (all must hold) |
|---|---|
| **Supported** | (a) n_flag ≥ 100 and ≥ 40 tickers; (b) `LB_95(π̂) > 0.70`; (c) paired lower bound of precision difference versus every baseline > 0; (d) profit claim holds (net return LB > 0, drawdown inside `10`); (e) the unknown-as-miss sensitivity still has `LB_95 > 0.70`; (f) each of the two sealed eras has a point estimate ≥ 0.60 (no single-era result); (g) replication on later data does not contradict (point estimate within the primary interval). Until (g) is available the label is "Supported, pending replication." |
| **Not supported** | n_flag ≥ 100 and the **upper** bound `UB_95(π̂) < 0.70` (interval is tight and below hurdle), or the primary bound passes but a baseline is not beaten in (c) on a tight interval. |
| **Underpowered** | Anything else: n_flag < 100 or < 40 tickers; or `LB_95 ≤ 0.70 ≤ UB_95` (interval straddles the hurdle); or the interval width (UB − LB) > 0.20 at the end of the extension. Reported as "could not tell," never as a pass. |

Edge cases: if (b) holds but (d), (e) or (f) fails, the verdict is **Underpowered** with the failing condition named (not Supported), unless the failing quantity has a tight interval below its bar, in which case Not supported. The paper-style output is the same for all three (`24`).

**DECISION NEEDED (D7): single-era rule (f).** Default: require ≥ 0.60 point estimate in each era. Alternative: drop (f) and report era results descriptively only, which is easier to pass and weaker as a claim.

## 11. Sealed test period

Two disjoint blocks, one per era, because WSB behavior has a regime break at January 2021 (`15`, `17` decay split). A single pooled period on one side of the break would let the claim hold in only one regime, or let one era dominate the cluster count.

| Block | Dates (inclusive) | Era | Why |
|---|---|---|---|
| A | 2020-01-01 to 2020-12-31 | Pre-2021 | Full year before the break, includes COVID volatility and retail growth, 2019 to 2021 are the active years in `28` |
| B | 2021-07-01 to 2022-06-30 | Post-January-2021 | Starts after the January to June 2021 meme peak is over, so it measures the post-break regime, not the single squeeze event; includes a falling market |
| Extension (once, section 9) | 2023-01-01 to 2023-12-31 | Post | Used only if n_flag < 100 |

- **Purge and embargo.** 20 trading days on each side of each block are dropped from training and from the sealed set (the 10-day label window overlaps the boundary). Train/validation use data outside blocks and embargoes only.
- **Time order.** Because the blocks are interior, training uses data both before and after a block. This weakens the "out-of-time" claim for the interior blocks. It is why replication (`24`, forward-in-time live data, paper only) is required for the final "Supported," and why the sealed set is touched once.
- **January to June 2021 is deliberately outside the sealed set**, in the exploratory data. It is the highest-volume, least typical period (`28`: 4,624 cashtag posts in one month versus 731 in 2026), and putting it in the sealed set would let a few meme tickers dominate the clusters. The per-ticker cap in section 12 also applies.
- The sealed period is not pulled with outcomes until freeze. Posts may be pulled and S computed; **prices for dates inside the blocks are not joined.**

**DECISION NEEDED (D8): sealed dates.** Default: the two blocks above. Alternative: include 2021-01 to 2021-06 in block B for more supply (about 2,900 ticker-days a month), accepting meme dominance; or put the sealed block at the latest data (2025-2026) for a cleaner out-of-time claim and a single era.

## 12. Exclusions

Applied before unsealing, by code frozen in the commit; counts reported by reason.

| Exclusion | Rule |
|---|---|
| Single-letter tickers | Drop cashtags of length 1 (`$A`, `$F`, `$T`, ...) because of false matches. Length-2 tickers pass only if they are on the listed-ticker file and not a common English word on a frozen list. |
| Removed or deleted bodies | Posts with body `[removed]` or `[deleted]` or an author `[deleted]`: **title-only** if a cashtag is in the title, otherwise excluded. Removed rate is reported per sub and era (`25`: 7 to 47%, and removal may correlate with outcomes). Sensitivity: rerun excluding all removed. |
| Liquidity floor | At day `d`: close ≥ $1.00, 20-day average dollar volume ≥ $500,000, market cap ≥ $50 million where available. Below this rows are excluded (the hit is not tradable, `10`). |
| Missing price data | Fewer than 150 prior days (beta window) or missing prices in the window (including delisting inside it): unscored, counted. Delisted coverage is checked first (`17` item 5); if coverage is poor, survivorship is reported as a limitation. |
| Catalyst confounds | Per section 5. |
| Ticker cap | No single ticker above 2% of flagged units in the primary count (the rest kept for sensitivity), per `17` fame-bias cap. |
| Non-US-listed or OTC-pink | Excluded (price source coverage). |
| Duplicates and bots | Cross-posts of the same text on the same day are one mention. Authors flagged by the frozen bot list are dropped. |

**DECISION NEEDED (D9): liquidity floors.** Default: price ≥ $1, ADV$ ≥ $500k, market cap ≥ $50M. Alternative: a stricter $5 and $2M, which suits "tradable" better but removes most of pennystocks and smallcapstocks (`25`: those subs have the highest cashtag rates).

## 13. What counts as a deviation

A **deviation** is any departure from this file after freezing. Each is logged in section 14 with date, reason, and a flag "before unsealing" or "after unsealing."

- **Major (invalidates the confirmatory label, result reported as exploratory):** any change to U, S, C, hit definition, benchmark, thresholds, null, test, alpha, H, sealed dates, or exclusions made after seeing any sealed outcome; re-running the sealed test with a changed spec; evaluating more than once; reading sealed outcomes before freeze.
- **Minor (allowed, logged):** bug fixes that do not change a definition (for example a date parsing error) found without looking at sealed outcomes; pull retries and API outages; a ticker-file update that is applied identically to all periods. A minor change needs a one-line justification and a diff of counts before and after.
- **Not a deviation:** reporting additional descriptive analyses clearly marked exploratory.

If a major deviation occurs, the original pre-registered analysis is still run and reported next to the new one.

## 14. Freeze record (to complete at freezing)

| Field | Value |
|---|---|
| Date and time frozen | |
| File hash of this document | |
| Code commit | |
| `label_version` | |
| `data_snapshot_id` | |
| Exploratory trial count `T` (`12`) | |
| Validation flag rate and cluster inflation | |
| Placebo `p0` and `p_b` with intervals | |
| Deviation log | |

## 15. DECISION NEEDED summary (Eli)

| # | Item | Recommended default |
|---|---|---|
| D1 | Universe breadth | All 14 subs |
| D2 | Model class | Regularized logistic on ticker-days |
| D3 | Window and threshold | 10 trading days, CAR ≥ +3% and above placebo 95th percentile |
| D4 | Benchmark | Market plus sector ETF |
| D5 | Alpha and search penalty | 0.05 one-sided, with trial-count penalty |
| D6 | Minimum n and extension | 100 flags from 40 tickers, one extension block |
| D7 | Single-era requirement | Point estimate ≥ 0.60 in each era |
| D8 | Sealed dates | A: 2020; B: 2021-07 to 2022-06; extension 2023 |
| D9 | Liquidity floors | $1, $500k ADV, $50M cap |

Also open and not decided here: how the profit claim's cost floor is set (`10`), and whether the hurdle `H` should be lowered if the placebo-derived `p0` turns out far above 5%.
