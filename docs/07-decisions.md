# 07 - Decisions so far

## Current state (October 14, 2026, authoritative with `38`)

- Source: Reddit via Arctic Shift census, 14 subs, 2012 to 2026 (`25`, `27`).
- Tickers first; repo and GitHub outcomes are deferred (`30`).
- Stage 1 is post-only; no comment pull for now (`28`).
- Price enters through labels only, never as a feature (`35`, `38` D9).
- Unit is the ticker-day (UTC date); decision time is 00:00 UTC next day (`38` D2).
- Primary claim (D1): net abnormal return lower bound over matched controls, 10-day window, 20 bps cost.
- Clustering is two-way (ticker and week); trial ladder at most 20 with Holm (D4, D6).
- Live input conversion contract (D12): one code path, hashed feature spec, parity test.
- Live prices free first; paid delisted data required before confirmatory (D10, USER decision).
- GitHub outcomes deferred; pre-registration v2 lives in `32`, not frozen.
- Laptop-first; raw data outside Dropbox (`C:\Users\dalele\dund-data`); `DUND_SALT` required.
- Reading order: `07, 38, 24, 32, 28, 31, 25, 27, 37`.

## Dated updates

### October 14, 2026: census probe finding
- Arctic Shift API pulls for the 14 subs run to `posts_v3`; paging uses an exclusive `after`, so the pager steps back one second and dedupes by id (`38` D15). QA compares monthly counts with an independent day sample. Ticker-day counts so far are partial (`36`).

### October 14, 2026: review outcome
- Four independent reviews (docs, data model and labels, statistics, code) led to `38`, the single source of truth. Older docs get a SUPERSEDED banner; nothing is deleted.

### October 14, 2026: decisions in 38
- D1 net-return claim, D2 ticker-day unit, D3 single 10-day window, D4 matched controls and two-way clustering, D5 purged splits, D6 trial ladder, D7 to D8 outcome-free gates and real-estimand power, D9 point-in-time allowlist, D10 coverage and delisted data, D11 removed bodies, D12 live input contract, D13 salt and privacy, D14 document policy, D15 census paging.

## Archived early decisions (superseded October 14, 2026, see 38)

- **Two tracks on one engine** (default). Track A (primary): AI and developer tooling with GitHub outcomes. Track B (cheap parallel test): crypto tokens that have repos, with no Reddit data. Stocks and options come later and only if a kill test passes. See `01`, `09`, `13`.
  - Replaced by: tickers first, post-only stage 1 (`38`, `32`).
- **Build budget $200, upkeep $25 per month.** Phase-1 LLM spend capped at $60 (default).
  - Replaced by: laptop-first with free sources, paid delisted data a pending USER decision (`38` D10).
- The $60 LLM cap covers the orchestrating agent's own tokens: data tasks capped at $15, orchestration at $35, reserve $10 (`10`, `11`).
  - Replaced by: same as above (`38` D10).
- Live data comes from a custom collector (PRAW with OAuth), not from the monthly dump.
  - Replaced by: Arctic Shift census (`27`, `38`).
- **Kill test K1 first** (default): does early GitHub growth precede abnormal returns in mapped assets, with placebo dates? A null result means "no large effect," given low power (`13`).
  - Replaced by: net-return lower bound vs matched controls (`38` D1, `32`).
- Phase 1 policy: weekly top-k review queue. Phase 2 policy (default): act only if the lower confidence bound on precision is at least breakeven plus 0.20, with a default payoff scenario of G = L = 100%, so the target is 0.70. Details in `10`.
  - Replaced by: break-even precision margin (`38` D1).
- Reddit history comes from the public git repo covering 2005 to 2026, filtered to the seed subreddits (`11`). Reddit data is used for training.
  - Replaced by: Arctic Shift census of 14 subs, 2012-2026 (`38`, `25`).
- Track B is in scope (stated). Agent billing: subscription preferred (stated). Hand-labeling budget: about 1 hour (stated). The agent does the pulls.
  - Replaced by: tickers first; Track B and GitHub deferred (`38` section E).

## Earlier decisions (history kept; where they conflict with the sections above, those win)

What has been settled. Each item can be reopened. Items marked (default) were chosen by Claude on Eli's instruction to answer what it could, and can be overridden.

## Framing

- Looking for **early trend indication**, not claiming posts cause outcomes.
- Experiment, not a trading system. No personal money for a long while, and only after the gates in `10` are met.
- The "one in a million" figure was a rough guess and is not treated as ground truth. The real rate gets measured.

## Scope and resources

- AI/dev tooling was chosen because its outcomes are measurable and free, not because its market upside is proven. The profit link is unproven.
- Seed subreddits: chosen from verified data (default). See `09`.
- Hardware: the school laptop is for analysis and review. A second, older ThinkPad with more storage is dedicated to the collector and long pulls (specs pending). VPS stays as backup. Options in `08`.
- Huginn is not part of the plan.

## Labels and outcomes

- Focus mostly on **outcome-based labels**, verified with outside data.
- Success definition (default): top 5% of the cohort on the primary outcome, with top 1% and top 10% as variants to compare.
- GitHub outcome (default): star gain over 12 months, ranked as a percentile within the cohort of repos first mentioned in the same month. Secondary signals: growth at 3 months, repo still active at 12 months, later citations.
- Credit rule (default): first mention only.
- Later citations of old posts are used to find and validate positives, never as features.
- Multiple signals are combined using **weights**, not a hard "all signals must agree" rule.
- A weight per data point acts as a confidence score over the weights themselves, to reduce the risk of fitting noise.
- **Score every mention**, including failures.
- Confounded cases (right outcome, different reason) are handled as an explicit edge case.
- Label model: write our own (default).

## Time

- Train on older data, test on newer data, with a gap equal to the longest horizon.
- Weight by time period. Decay half-life chosen on validation folds from the grid 1, 2, 3, 4, 6 years, starting guess 3 years (default).
- Measure outcomes in **event time**, not calendar year.
- Horizons: checkpoints at 3 and 12 months, compare 24 months (default for GitHub).
- "Only new data" is tested, not assumed: recent-only vs all-with-decay.

## Risk

- **Risk averse.** False positives are very bad. False negatives are acceptable.
- A missed positive noticed later is a useful hard example, not a loss.
- Everything is risk adjusted, and **confidence scores are required in the final output**.
- Sizing (default): at most 1% of capital per alert and at most quarter Kelly, with the whole experiment limited to a small sleeve.
- No money until the research, live, and money gates in `10` are met.

## Model and data

- Regularized logistic regression first.
- Weights for user, subreddit, certain words, and events around the time, learned from data.
- For users with little history, use their connections (subreddits, topics) as a prior.
- Use only information available at posting time as features.
- Entity resolution (default): URL-first for repos. Tickers only with a `$` prefix or in finance subs, with ambiguous short tickers excluded.

## Data collection

- Arctic Shift is a secondary source.
- Start the live collector early.

## Profit link, evaluation, and pivot

- If the profit link fails, the engine stays as a **tool radar** feeding your own tools. The signal model never depends on the asset mapper, simulator, or dashboards (`01`, `13`).
- Two dashboards (default Dash, `12`): the **Truth board** (honest accuracy: walk-forward, permutation tests, sealed test period unsealed once, trial counter, luck meter) and the **Sandbox** (acceptance line, all trades in a period, industry filter, sort keys). Build the harness on synthetic data first.
- POC extraction is **link-only** (GitHub URLs), no name-based extraction.
- Agent runs follow stages S0-S9 with human gates G0-G4 and a spend gate at 80% (`11`).
- Options are not in the POC (default).

## Input point and confidence (new, October 13, 2026)

- The **post** is the input row, with repos and other entities checked along the way when mentioned. Each post gets an impact label `p` and a confidence `c = decisiveness x evidence quality`, and training weight uses `c`. Spec in `16`. Supersedes the repo-first framing in `14` section 2.

## Target and data source (October 13, 2026)

- Target: a financial logistic model mapping posts to market shifts as early indicators. Weighting standard and voter priors are in `17`.
- Dataset: Arctic Shift (GitHub `ArthurHeitmann/arctic_shift`, torrents on Academic Torrents, about 3.8 TB for 2005 to 2025-12). Not downloaded; filter by subreddit and month (`17`).

## Compute and output (October 13, 2026)

- Everything runs on the current laptop; cloud only for what it cannot hold (bulk ingest, scheduled collectors). The laptop has about 3 GB free disk, so bulk data is cloud-side and out of Dropbox (`18`).
- Final output: a report of what to do with a confidence score defined as the margin above the decision threshold (`18`).

## Variables, subs, and open-item defaults (October 13, 2026)

- About 60 candidate variables in 7 feature groups, user types as behavioral archetypes, a wider subreddit scan list (finance, tech, company, science), and defaults for the open items. All in `19`.

## Subreddit waves (October 13, 2026)

- Scan in waves by a scored prior, not all 86 at once. Wave 1 is the 14-sub census (see `25`, `38`); the earlier "about 23 subs" figure is superseded. More waves are added only if projected data is short. Scores are priors until R0 counts exist. See `20`.

## Subreddit as a variable (October 13, 2026)

- Subreddit is a model input (group D in `19`), so training learns per-sub weighting. The waves in `20` only decide what to pull and in what order. They are not a hard filter on what the model may learn from.

## Sampling (October 13, 2026)

- Pull full date-complete census per sub, ordered by time. No top, hot, or score-based pulls. Train-versus-live representativeness checks gate any model fit. See `22`.

## Unicorn examples are for variable design only (October 13, 2026)

- Good-example hunting informs which variables to build and gives an evaluation slice. It does not define the training sample. One transform path serves training and live input, with a parity test. See `22`, `15`.

## Explore first, then test (October 13, 2026)

- No evidence yet for where signals live. Scores in `20` only order the work. Data need is much larger than first estimated, with a pre-registered detection test and kill criteria. See `23`.

## Research framing (October 13, 2026)

- The project is a hypothesis test as much as an algorithm. H1: some signal set S in a source universe U gives an early call C with hit-rate lower bound at confidence level L above hurdle H and baselines, plus a separate profit claim. Exploratory, confirmatory, replication phases; verdicts supported, not supported, or underpowered. See `24`.

## R0 pilot run (October 13, 2026)

- A one-month census of 14 subs was pulled through the Arctic Shift API (about 16,800 posts). Findings and plan changes in `25`. No signal tests were run.

## Focus on tickers; live-ticker prices first (October 14, 2026)

- **Stock side only for now.** Repo and GitHub-star outcomes (GH Archive, BigQuery) are deferred until the ticker side shows any signal. See `30`.
- **Prices:** start with live (still-listed) tickers from free sources. Delisted names are missing, so the first pass is exploratory and carries a survivorship caveat. A cheap paid historical dataset with delisted coverage is planned for before the confirmatory phase. Not yet priced. See `29`.
- **Comment-introduced tickers** (a comment names a ticker the post did not) are kept as a later event type, dated at the comment, not the post. Measured at about 4% of posts in a small sample. Build after the resolver runs on real census data. See `28`.
- **Pre-registration:** draft with nine default decisions in `32`. Not frozen. Freeze before any outcome data is joined.
- **Census:** full-history post pull for 14 subs running into `posts_v3` under the local dund-data folder. Raw data stays outside Dropbox and out of git.

## Reddit access (new)

- Optional live API read of chosen subreddits, about daily, scored by the frozen model. Rules in `11`.

## Process

- Do the sample-size (d vs N) math before building the training and test suite (done, `05`).
- This will be long, expensive work. Use a funnel with spending caps.
- Output format (default): weekly markdown or HTML review report plus a CSV for your judgments.
