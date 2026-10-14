# 22 - Representativeness and sampling

Decision of October 13, 2026 (Eli): the training data must match the inputs the model will see later. No pulling "top" posts, because that skews the sample. This sets how we pull, what we compare, and what blocks training.

## Principle

The model will score **every new post in the scanned subs as it arrives**, with no knowledge of how it will do. So the training rows must be drawn from the same population: all posts in the scanned subs, at the age and in the state a new post is in when scored. Any selection that depends on how a post later performed (score, comments, awards, front-page, being linked later) puts the answer into the sample.

## Pull rules

1. **Census, not ranking.** Pull every post in a sub for a date range, ordered by `created_utc`. Never `sort` by score, never use "top", "hot", "controversial", or a minimum score or comment count. With the Arctic Shift API: `subreddit`, `after`, `before`, `sort=asc`, page with the last `created_utc`.
2. **Date-complete windows.** Pull whole months, not "until we have enough". A partial month overweights its first days and skews day-of-week and event coverage.
3. **Same rules for every sub and period.** Same fields, same filters. A different rule for a small sub is a bias that looks like a sub effect.
4. **Keep removed and deleted rows** (flagged), not just the survivors. Removed posts are often spam and promo, which the model will see live.
5. **No keyword pre-filter at pull time.** Do not fetch only posts that already contain "github" or a ticker. That decides the answer to "has a link" before modelling. Extract links after, from the full census, and keep the posts with no link as type C (`16`).
6. **If a census is too big,** take a **random sample within sub-month strata** with a stored seed and inclusion probability, and keep inverse-probability weights. Do not sample by popularity.
7. **Store the whole pull, with its manifest:** query, date range, request count, rows returned, and gaps. Nothing is dropped except at the reduction step, which is itself logged.

## Where skew can still creep in

| Source of skew | Why it matters | Control |
|---|---|---|
| **Score and comment counts are ingestion-time or settled later** (API: 0 or 1 at first, matching dumps after about 36 hours) | Training on final scores but scoring live at hour 1 is a train/serve mismatch, and final score is itself an outcome | Score and comments are not features from the census (`04`, `19` F6). Early-dynamics features come only from live snapshots |
| **Survivorship: deleted, removed, or banned authors and subs** | Failures vanish from the data | Count removed share per sub-month, compare across years, keep flagged rows |
| **Archive gaps** | A gap month looks like a quiet month | Compare posts per sub-month with expectation from neighbors and the subscriber snapshot. Flag gaps and exclude them from "first mention" logic (`14`) |
| **Sub selection** (waves, `20`) | We chose subs partly by expected yield | Report results by wave, keep the control subs, and never describe results as "Reddit" in general |
| **Entity resolution coverage** | Easy entities resolve (clean URL, cashtag), hard ones do not, so resolved rows are not the population | Compare resolved vs unresolved on content and sub features. Report the resolved share by sub and year. Use weights (`16`, resolution factor) |
| **Outcome data coverage** | Thin or missing prices and delisted assets drop the failures | Report outcome availability by cohort. Missing-not-at-random handling: keep rows with an "unobservable" flag, do not silently drop |
| **Time drift** | Platform and user behavior change (2021, 2023) | Regime flag (D6), rolling-origin validation, per-year reports |
| **Right-censoring** | Newest rows lack outcomes | Unknown, not negative (`04`) |
| **Cross-posts and duplicates** | Overweight popular items | Group and count once (`14`) |
| **Bots and promo** | Different from real submissions | Flag, keep, report with and without |

## Representativeness checks (go / no-go before any model fit)

Run on the training table versus a **live sample** (the first weeks of the live collector, or the newest unlabeled months of the dump as a stand-in).

| Check | How | Rule (placeholder) |
|---|---|---|
| Sub mix | Share of posts per sub, train vs live | Max absolute difference under about 10 points. Otherwise reweight by sub |
| Post-type mix | DD, question, link, meme shares | Similar test |
| Feature distributions | Two-sample test or population stability index for each feature in the registry | PSI under about 0.2 per feature, or a documented reason |
| Time-of-day, day-of-week | Hours and weekdays | Similar test |
| Missingness | Share missing by feature, train vs live | Differences explained |
| Resolution rate and entity mix | Resolved share, ticker vs repo vs token | Differences explained |
| Adversarial validation | Train a classifier to tell train rows from live rows using the features | AUC near 0.5. A high AUC lists the features that differ, and those are the drift suspects |
| Label base rate by year and sub | Positive rate per stratum with intervals | No unexplained jumps |

If a check fails, the first response is to **fix the pull or reweight**, not to tune the model.

## Weights and strata when we cannot fix the sample

- Importance weights `w_i = P_live(x) / P_train(x)` from a probabilistic classifier on the covariates (sub, type, age, size band), clipped at a stated maximum to avoid a few rows dominating.
- Report effective N after weighting (`04`) and refuse a fit when it drops below the budget in `05`.
- Report headline metrics both unweighted and weighted, and by stratum.

## What this changes in the R0 plan

- R0 pulls a **full month** for two or three subs by date order, with no score filter, so we can measure real post counts, removed share, link share, and field semantics.
- R0's output includes a representativeness first pass: posts per day, hour-of-day, post-type mix, removed share, and the retrieved-time lag.
- Only after R0 is read do we choose strata for the larger pull.

## One transform path for training and live input (added October 13, 2026)

The reason the hunt for good examples mattered was to know which variables to look for. That is a design input, not a sampling rule. Consequences:

1. **Unicorn cases are used three ways only:** to propose variables (hypotheses in the discovery log, `19`), to build an evaluation slice that checks the model finds known early signals, and to sanity-check labels. They are never the training sample.
2. **Training data is the census** (above), with its natural base rate and its natural dud-heavy mix.
3. **Raw to model-ready is one code path.** Whatever transformation turns a raw post into features (link extraction, entity resolution, market context lookup, archetype assignment) is the same function in training and in live scoring. The live collector emits the same raw record shape as the dump, and a "live record" goes through the identical function.
4. **Transformations are versioned and recorded** in each row (`transform_version`, `data_snapshot_id`), so a feature change is a new version, not an overwrite.
5. **Parity test:** feed a sample of dump rows through the live ingestion adapter, run the shared transform, and require the output to equal the training-table values (within a stated tolerance). A failure blocks the release of any scoring job.
6. **Where the dump lacks something live has** (score at one hour), the transform leaves it missing in training, and the model never uses it (`19` group F stays live-only).
7. **Where live lacks something the dump has** (final score, later comments), the transform never produces it for training features either.
