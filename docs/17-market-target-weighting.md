# 17 - Weighting for a market-shift target

Decision of October 13, 2026. Goal restated by Eli: **train a financial logistic model that maps posts to shifts in the market, as early indicators.** Every weight below is judged against that standard. This reorders the voters in `16` (repo outcomes become supporting evidence, market outcomes become primary). All numbers are starting priors to be re-fit on earlier years and frozen (`04`); none are measured.

## Data source (found October 13, 2026)

- Arctic Shift, GitHub: `https://github.com/ArthurHeitmann/arctic_shift` (tooling, scripts, and link pages). Data is distributed by torrent through Academic Torrents, not stored in git.
- Combined archive 2005-06 to 2025-12: magnet length `xl=3804096351995` bytes, about **3.8 TB**. Monthly files from 2026-01 to 2026-09 are listed separately. Infohash `3d426c47c767d40f82c7ef0f47c3acacedd2bf44`.
- Links page: `https://github.com/ArthurHeitmann/arctic_shift/blob/master/download_links.md`. A separate tool for downloading specific subreddits or users, and an API, are linked from the repo README (verify limits).
- Plan (verify before acting): do **not** pull the whole archive. Use the per-subreddit download tool or per-month files, submissions only to start, filter streaming to the scanned subs, and keep reduced Parquet only (`11`). Nothing has been downloaded.

## Standard for a "yes"

A post is a positive only if the **market moved after it, beyond what chance and the market itself explain**, and the post came before the move:

| Requirement | Rule (placeholder) |
|---|---|
| Abnormal return | Cumulative abnormal return versus a benchmark that adjusts for market, sector, and beta (e.g., CAPM or sector ETF), over fixed windows after the post |
| Beyond chance | Exceeds the 95th percentile of placebo windows for the same asset on random non-post dates (`13` K1) |
| Tradable | Passes liquidity and size floors from `10` at the post date |
| Early | Post precedes the start of the move (lead rule, `16`) |
| Not explained elsewhere | No dated catalyst the post did not mention (earnings, M&A, FDA), else confounded and `q` is cut (`16`) |

A "no" requires an affirmative non-move (CAR inside the placebo band). Between the two bands the row is **unknown** and gets low `c`, not a hard no. This is what keeps false positives cheap to avoid and false negatives acceptable (`04` risk posture).

## Voter weights (priors, sum 1)

| Voter | Prior weight | Why |
|---|---|---|
| CAR at 1 to 20 trading days, placebo-adjusted | 0.35 | Closest to "early indicator of a shift," and the least contaminated by later news |
| CAR at 21 to 63 days | 0.25 | Persistence of the shift |
| CAR at 64 to 252 days | 0.15 | Longer drift, more confounded, lower weight |
| Lead rule (post before move start) | 0.10 | Timing is the point of an early indicator |
| Linked-entity fundamentals (repo growth for company-owned repos, token repo activity) | 0.10 | Mechanism evidence, never sufficient alone (`13`: no evidence yet that repo growth predicts returns) |
| Later citations of the post (label side only) | 0.03 | Visibility bias |
| Post attention effect | 0.02 | Reach, not truth, and can be caused by the post |

Confounder flags are not a voter. They scale `q` multiplicatively, so a confounded win cannot be voted back in.

## Per-example training weight

`w = c × decay × materiality × cluster_share × cap`

| Factor | Rule | Reason |
|---|---|---|
| `c` | From `16` | Label certainty |
| `decay` | `0.5^(age/half-life)`, half-life by validation, separate before and after Jan 2021 (`15`) | Regime break in WSB behavior |
| `materiality` | Rises with the asset's sensitivity to the entity (company-owned > thematic > unrelated), floored at 0.2 | A post about something that barely moves the stock should not teach a strong effect |
| `cluster_share` | `1 / sqrt(k)` where `k` is the number of posts on the same asset within the same window | Posts about one ticker-day are not independent, and effective N is closer to the number of asset-events |
| `cap` | No single ticker or event above 2% of total weight | Fame bias (`15`) |
| Negatives | Multiply weight of confident negatives by about 1.5 initially, then recalibrate | False positives cost more than false negatives (`04`) |

Report `N_eff = (Σw)² / Σw²` and the number of independent asset-events. The d versus N budget (`05`) is set by asset-events, which will be much smaller than the post count.

## Decisions that follow

1. **Primary entity is the tradable asset** (ticker or token). Posts that only mention a repo count through the repo-to-asset map (`13`); unmapped repo posts feed the tool radar and carry zero weight in the market model.
2. **Market model and tool radar are separate models** sharing the post table. A post can have both labels.
3. **Horizon set is short-first** (1 to 20 days) for the market model. The 12-month star-gain label stays for the tool radar.
4. **Benchmarks and placebo draws are part of the label code** and versioned with `label_version` (`16`).
5. **Free price data** (Stooq, CoinGecko, FRED) has survivorship and adjustment limits; check delisted coverage before trusting any backtest (verify).

## Open items

1. Benchmark choice: single market index, sector ETF, or a factor model? Default: market plus sector ETF.
2. Whether to include options and short interest as features and outcomes (out of scope for now).
3. Materiality scoring inputs (market cap band, revenue share of the product, open-source dependency). Needs the S5 org-to-ticker table.
