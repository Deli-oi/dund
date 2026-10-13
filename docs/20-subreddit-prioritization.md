# 20 - Subreddit prioritization: which ones to scan

Written October 13, 2026. Answers "do we need to monitor all of those?" No. This ranks the 86 subreddits in `19` by an estimated likelihood of containing a real early indicator, then sets how many to scan from how much training data we need. **Every score is my prior, not a measurement.** None of these subs has been pulled or profiled. Wave membership gets revised after the first counts (`14` section 5).

## Scoring rubric (1 to 5 each, then 0 to 100)

| Factor | Weight | 5 means |
|---|---|---|
| Checkable (C) | 0.30 | Posts usually name a ticker, token, or repo that has free outcome data |
| Early (E) | 0.20 | Small or niche enough that first mentions happen here before general subs |
| Information quality (I) | 0.20 | Sourced analysis or builders showing work, not hype |
| Volume and history (V) | 0.15 | Many posts, long history, covers pre-2021 |
| Contamination (X, inverted) | 0.15 | 1 = low risk of pumps, attention loops, or promo; 5 = high |

`score = 100 × (0.30·C + 0.20·E + 0.20·I + 0.15·V + 0.15·(5 − X)) / 5`. The script is in the session scratchpad. Reproduce it from this table if needed.

## Ranking (top 43 of 86, the first two waves)

| # | Score | Subreddit | C E I V X |
|---|---|---|---|
| 1 | 84 | SecurityAnalysis | 5 4 5 2 1 |
| 2 | 83 | ValueInvesting | 5 3 5 3 1 |
| 3 | 83 | MachineLearning | 4 3 5 5 1 |
| 4 | 79 | coolgithubprojects | 5 5 2 4 2 |
| 5 | 79 | LocalLLaMA | 4 3 4 5 1 |
| 6 | 77 | smallcapstocks | 5 5 3 2 2 |
| 7 | 76 | AMD_Stock | 5 3 4 3 2 |
| 8 | 74 | mcp | 4 5 3 2 1 |
| 9 | 73 | NVDA_Stock | 5 3 4 2 2 |
| 10 | 73 | biotech | 4 3 4 3 1 |
| 11 | 72 | teslainvestorsclub | 5 2 4 3 2 |
| 12 | 71 | selfhosted | 4 2 3 5 1 |
| 13 | 71 | ollama | 3 5 3 3 1 |
| 14 | 69 | Vitards | 4 5 4 1 3 |
| 15 | 68 | opensource | 4 2 3 4 1 |
| 16 | 68 | investing | 4 2 3 5 2 |
| 17 | 68 | ethfinance | 3 4 4 2 1 |
| 18 | 67 | netsec | 3 3 4 3 1 |
| 19 | 67 | LocalLLM | 3 4 3 3 1 |
| 20 | 67 | LangChain | 3 4 3 3 1 |
| 21 | 67 | LLMDevs | 3 4 3 3 1 |
| 22 | 67 | BiotechStocks | 4 4 3 2 2 |
| 23 to 43 | 66 down to 60 | rust, hackernews, golang, SideProject, stocks, programming, Python, OpenWebUI, venturecapital, Stock_Picks, Rag, startups, neovim, commandline, kubernetes, hardware, docker, StableDiffusion, defi, QuantumComputing, SPACs | |

The remaining 43 (ranks 44 to 86) are wave 3.

## Where I override the score

| Sub | Score said | Override | Reason |
|---|---|---|---|
| r/wallstreetbets | #45 | **Wave 1, DD flair and similar post types only**, pre- and post-January 2021 reported separately | It is the best-documented source of real early signal (Bradley et al., `15`), and the rubric's whole-sub "information quality" hides that. Memes and YOLO posts are filtered out |
| r/pennystocks, r/CryptoMoonShots, r/SatoshiStreetBets, r/altcoin, r/Superstonk | #53 to #80 | **Negatives and attention controls**, small sample, not for positives | The model needs known pump and attention examples (`15` tier 4) |
| r/personalfinance, r/FinancialCareers, random large subs | Not scored | Base-rate controls, small sample | `19` |
| r/algotrading | #48 | Wave 2, kept | Builders, but few posts name tradable assets |

## How much data we need, and what that implies

| Quantity | Value | Basis |
|---|---|---|
| Features the model can carry | about 15 | `19` plus ablation |
| Effective positives needed | about 150 to 200 | 10 per feature (`05`) |
| Raw positives needed | about 1,000 to 1,500 | At the 18% retention assumed in `05` |
| Resolved-entity posts needed | **about 50,000 to 100,000** | Placebo threshold at the 95th percentile means a no-skill model still sees about 5% "positives". We need the excess above 5%. If the true hit rate is 7% against 5% null, we need about 70,000 resolved posts to see about 1,500 excess positives, and more if the lift is smaller |
| Share of posts that resolve to a tradable entity | about 3 to 10% in finance and company subs, about 1 to 3% in dev subs | Assumption. Measure at R0 |

Implication: precision is dominated by **finance and company subs**, where posts resolve to assets. Dev subs mainly feed the tool radar and the repo-to-company link.

## Waves and the rule for adding more

| Wave | Subs | Purpose | Move to next wave when |
|---|---|---|---|
| 1 | Top 22 plus r/wallstreetbets (DD) plus negative controls, about 25% | First counts, first model, leakage and baseline checks | Wave 1 projects fewer than about 60,000 resolved posts, or fewer than about 1,500 raw positives, or intervals are too wide to separate Reddit features from the repo-only baseline |
| 2 | Ranks 23 to 43 | More volume and more small communities | Same test, applied to wave 1 plus 2 |
| 3 | Ranks 44 to 86 and graph-discovered subs | Only to add specific coverage, such as a company or sector where wave 1 and 2 are thin | Marginal yield: adding a sub must raise projected positives by at least about 3% of the current total, or fill a regime or sector gap |

Order inside a wave does not matter for training. It matters for the first look, which uses one year of each sub to measure real post counts and resolution rates.

## Monitoring versus training

- **Historical training scan:** waves as above, from the dump. Streaming and filtered (`18`).
- **Live monitoring** (collector, daily): only subs that earn it. Rule: a sub joins live monitoring after wave 1 shows it contributed positives with a lead time of at least a few days. Expect 10 to 20 live subs, not 86. Free API limits (100 queries per minute, `11`) are not the constraint. Complexity and cost are.

## Caveats

1. **The scores encode my assumptions about sub culture.** Treat the order as a hypothesis. The R0 profile replaces my C, E, and V guesses with measured values first, since they are directly countable.
2. **Info quality and contamination are the least certain,** and can only be checked after labels exist. They are re-scored per sub from measured hit rate and confounder rate (computed on earlier years only).
3. **Selection by past yield is a form of tuning.** Re-scoring subs on outcomes must use only data before the validation period, and every re-ranking counts as a trial (`12`).
4. **Unverified names.** Most of the 86 have not been checked in the Arctic Shift API (`19`). Dropped or renamed subs just leave the list.
5. **Company-specific subs (AMD, NVDA, Tesla) have high checkability but strong fan bias.** Their positive posts may be enthusiasm with a good outcome by coincidence, so they are tested separately for lift over the asset's own trailing return.
