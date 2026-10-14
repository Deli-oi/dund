# 13 - From early signal to profit: mapping, evidence, and kill tests
> **Status: SUPERSEDED in part (October 14, 2026).** The project is now ticker-first, with GitHub-star outcomes deferred, and the study design and decisions in `docs/38-review-decisions.md` and `docs/07-decisions.md` override this document where they differ. Kept for history and for the sections not contradicted.

## The honest framing

The model's job is to say which repos or tools are likely to take off. Turning that into profit needs a second link: **a tradable asset whose price reacts to the repo taking off.** That link is the least proven part of this project. The data collection and the model can work perfectly and the second link can still be empty.

On "where is the most upside": I chose AI and dev tooling because its outcomes are easy to measure, not because I have shown it has the largest tradable upside. I do not know which domain does, and the evidence I found (below) is skeptical about retail-attention signals in general. The largest potential magnitude is probably in small-cap stocks and crypto tokens, which is also where manipulation and total-loss risk are highest. Because the POC is paper-only, the cost of testing both is low, so the plan runs a cheap test of the weakest link first and lets the data decide.

## Evidence found (read before believing any profit story)

| Source | What it examined | Finding | Caveats |
|---|---|---|---|
| Chacon, Morillon, Wang (2023), "Will the Reddit Rebellion Take You to the Moon? Evidence from WallStreetBets", *Financial Markets and Portfolio Management* | Stocks with r/wallstreetbets buy recommendations, 2012 to Q1 2021 | No abnormal returns. Long-short alpha statistically indistinguishable from zero at all holding periods, and the long portfolio was negative in every period | I read a summary (Alpha Architect), not the paper. Hypothetical returns |
| Lucchini et al. (2020), "From code to market: Network of developers and correlated returns of cryptocurrencies" (arXiv 2004.07290) | Developers who work on more than one cryptocurrency | Coins linked by a shared developer show synchronized returns in the following months | Correlation between linked coins, not a demonstrated forecasting tool |
| fffinstill blog, Reddit mentions vs stock returns | 4,483 ticker-day signals, Feb 27 to Apr 28, 2026, 5-day forward returns | Extreme mention spikes averaged -0.52% against a +0.44% benchmark | Company blog, 61 days, small buckets, no significance tests |
| "Place Your Bets? The Market Consequences of Investment Advice on Reddit's WallStreetBets" | Title seen in search results | Unread. The literature may be mixed | Not read |
| "The Private Value of Open Source Innovation" (ABFER 2025 conference paper) | Open source and firm value | Unread (fetch failed) | Not read |
| Practitioner posts on GitHub activity vs crypto prices (The Tie, CryptoScores) | Correlation analyses | Unread | Not peer-reviewed |

**Bottom line:** I found no evidence that early GitHub growth predicts returns in mapped assets, and the one careful study of retail recommendations found nothing. Absence in my search is not proof of absence, but it means expect a null result and design the project so a null result still leaves something useful.

## Two modules, so a null result does not sink the project

1. **Signal engine:** Reddit post to probability that a repo takes off. This is the thing that learns.
2. **Asset mapper and simulator:** repo to tradable asset to simulated trades. This is optional.

If the second module fails its tests, the first still has value as a **tool radar**: a feed of emerging open-source tools with probabilities, lead time, and topics. You mentioned possibly pivoting to open-source tooling only, to feed your own tools that need the newest tech. That pivot costs nothing in this design, because the engine and its feed are the same either way.

## Mapping types

| Type | How it works | Strength | Weakness |
|---|---|---|---|
| Direct, token | A token whose project has a GitHub repo. CoinGecko coin metadata lists repos (verify) | Clean mapping, tradable | Small universe, manipulation, survivorship in free price data |
| Direct, company | Repo owned by the GitHub org of a public company (open-core vendors, small and mid caps) | Clear owner | Few small caps, most owners are mega caps where one repo is immaterial |
| Thematic | Repo topic maps to exposed tickers through a curated exposure table | Large universe | Diffuse and weak, the effect on any one stock is tiny |
| Displacement | A repo replaces a paid product, so the incumbent is hurt | Plausible story | Needs short positions, high risk. **Out of scope** |

Each mapping gets a **materiality score**: how large the affected revenue or project value is relative to the asset's size. Mega-cap stocks fail this test almost by definition.

## Kill tests (cheap, run before building the whole pipeline)

### K1: does early GitHub growth precede abnormal returns in mapped assets?

- No Reddit data needed. Take repos with a mapped token or company, define "early growth events" (for example a repo entering the top 5% of star gain in its cohort), and run an **event study**: average abnormal return after the event against a benchmark (BTC or a sector ETF), versus **placebo dates** drawn at random for the same assets.
- Windows: 5, 20, and 60 trading days.
- Cost: $0 in model calls. Time: mostly the GitHub pull.
- **Decision:** if K1 shows nothing beyond the placebo band, shelve the profit module and keep the tool radar. No amount of model quality fixes an empty link.

### K2: do Reddit posts add anything beyond simple baselines for repo success?

- This is the original model compared against baselines such as subreddit growth rate. If it does not beat them, stop and rethink the features.

### Power: how many independent events K1 needs

Events needed to detect a mean abnormal return at a two-sided 5% level with 80% power. The standard deviations are assumptions, and events must be independent (clustered events need more):

| Return std dev at the horizon | Detect 2% | 3% | 5% | 10% |
|---|---|---|---|---|
| 10% (large-cap-like, 20 days) | 197 | 88 | 32 | 8 |
| 15% (small-cap, 20 days) | 442 | 197 | 71 | 18 |
| 40% (crypto, 20 days) | 3,140 | 1,396 | 503 | 126 |

Testing 10 configurations instead of one raises the need for a 5% effect at 15% std dev from 71 to 120 events, and 50 configurations to 154. So the number of variants tried must be logged and the bar raised accordingly (see `10`).

**Practical consequence:** crypto is noisy enough that a small real effect would take hundreds to thousands of independent events to detect, and a mapped-token universe may be too small for that. Small-cap equities need fewer events but have fewer mapped repos. Expect K1 to be underpowered for modest effects, which means a non-significant result will not prove the absence of an effect. It will only rule out large ones.

## Event study design (for K1 and later for live checks)

1. Define the event date as the first date the repo crosses the threshold, using only data available that day.
2. Define the trade date as the next market open after the event date (crypto: next day's open), never the same day.
3. Abnormal return = asset return minus the benchmark's return over the same window (a market model fit on a window before the event is better).
4. Compare against placebo dates and against matched assets without events.
5. Cluster standard errors by date (events in the same week share market moves).
6. Apply liquidity and cost assumptions from `12` before calling anything a gain.

## Open items

- Which free source gives delisted companies for equities (I could not confirm any, so equity results are optimistic by default). See `10` for the CRSP route.
- Whether CoinGecko's repo links cover enough tokens (verify).
- Whether the "Place Your Bets" paper's results change the picture on Reddit-attention signals (unread).
