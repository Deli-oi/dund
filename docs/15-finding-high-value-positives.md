# 15 - Finding high-value positives ("unicorn" data)

Written October 13, 2026. Extends `14`. Goal: find, on purpose, the posts that came before something big (a stock or token run, a repo that became a company), so training and the gold set are not left to whatever the random pull yields. Items marked (unverified) came from a search summary or my own knowledge and need a primary-source check before we rely on them.

> **Role updated October 13, 2026 (Eli):** the outcome-first search and the gold tiers below are for **variable discovery and for evaluation slices only**. They must not define the training sample, because selecting on good outcomes skews it (`22`). Training uses the full census. Unicorn cases tell us which variables to build and are a test slice for checking that the model finds them, not training rows.

## What the literature suggests (read before designing)

| Finding | Source | Effect on the plan |
|---|---|---|
| Before GameStop (Jan 2021), WSB "due diligence" posts predicted returns and cash-flow news. After it, predictability disappeared, and the drop was concentrated in reports emphasizing price pressure or attention-grabbing stocks. About 2,340 DD reports from 2018 to 2020 were studied. Working-paper version: buy DD recommendations followed by about 1.1% two-day abnormal returns | Bradley, Hanousek, Jame, Xiao, "Place Your Bets?" ([summary](https://www.cxoadvisory.com/?p=38197), [journal listing](https://scholars.uky.edu/en/publications/place-your-bets-the-value-of-investment-research-on-reddits-walls/)) | Treat **Jan 2021 as a regime break.** Train and report pre- and post-period separately. The pre-2021 DD corpus is the most promising positive source |
| A more skeptical view: little signal from WSB sentiment and DD about future prices, except for meme stocks | Oxford thesis ([link](https://ora.ox.ac.uk/objects/uuid:6f3c53d3-f0d6-4232-b3cf-bf1696b200f9/files/dsf268587w)) | Expect weak results and keep the null as a live outcome |
| "Attention cascades" on WSB associated with abnormal returns of about 5% without reversal (working paper) | Otsubo, Poon, Wei ([abstract](https://www.bayes.citystgeorges.ac.uk/__data/assets/pdf_file/0006/981321/Abstract-Yoichi-Otsubo,-Kobe-University,-Japan,-Ser-Huang-Poon,-University-of-Manchester,-UK,-and-Siliang-Wei.pdf)) | Attention is a feature and a confounder: the model may learn "crowd arrived" and not "information." Separate them |
| GameStop intraday: posts relate to trading measures, but the effect is attention, not informativeness. A small group of influential posters drove much of it | IIM Bangalore WP 644 ([pdf](https://www.iimb.ac.in/sites/default/files/2021-12/WP%20No.%20644.pdf)) | Author concentration is a feature and a leakage risk |
| Open-source engagement on GitHub is associated with early-stage startups later getting funded (matched sample). No rigorous study found showing star counts alone predict funding or acquisition. Stars are buyable, and fake-star campaigns have appeared on Trending | Search summary, [Indie Hackers thread](https://www.indiehackers.com/post/after-product-hunt-founders-are-trying-to-game-github-8acae39f84) (weak) | The tool-to-company link is plausible but unproven. Use contributor and activity features, not stars only, and flag fake stars (`14`) |
| Runa Capital's ROSS Index ranks open-source startups by star growth and is said to predict funding rounds (second-hand, unverified) | Same thread | Candidate seed list for "repos that became companies"; verify with Runa |

The honest read is that the best positive evidence is narrow: pre-2021 WSB DD about specific companies, and open-source engagement preceding funding.

## 1. Search outcome-first, then walk backward

Random sampling of posts makes unicorns too rare. Reverse it: define the outcome universe from outside data, then ask "who mentioned this first, and when?"

| Domain | Outcome universe (build from) | Backward search |
|---|---|---|
| Stocks | Top 1% to 5% of 12-month excess return per year (Stooq or other price source, verify), with liquidity and market-cap floors. Plus acquisitions at a premium (SEC 8-K, EDGAR full-text search), FDA decisions, index adds, first profitable quarters | Earliest Reddit mention of the ticker or company name before the run began, within the dump |
| Tokens | Top performers per year on CoinGecko with a repo (verify metadata coverage) | Earliest mention of the token name or repo |
| Repos and tools | Top 1% of 12-month star gain in the cohort (`11` S2); repos that became funded companies or were acquired (Crunchbase, YC list, press: verify access and cost) | Earliest mention of the repo URL or project name |
| Companies from the open-source side | Company-owned repos that grew fast, joined to public ticker (`13` K1b) | Mentions of the repo before the stock moved |

**Output per positive:** earliest mention, lead time in days before the run started, subreddit, author, post type, and whether the mention was substantive (DD, thesis) or a passing name-drop.

## 2. The survivorship trap and how to avoid it

Outcome-first search finds hits and says nothing about misses. A model trained on it learns "posts that mention things that later won," which is a description of the past and not a predictor.

- **Every positive needs matched negatives drawn from the same pull.** Same subreddit, same month, same type of mention (DD, question, news link), same market-cap band or repo age band, and an outcome that fell below the cutoff. Matching is done before looking at later outcomes where possible.
- **Mentions are the denominator.** Hits found backward are only used as a validation of the label and to select gold cases, not as the whole training set. The training set remains "every mention" (`04`).
- **Lead time distribution.** Report how many positives were mentioned before the run and how many only after. A model that only finds "already moving" cases is a momentum detector.
- **Fame bias.** The famous cases (GameStop, a few viral calls) will dominate. Cap the weight of any single ticker or repo, and report results with the top 5 cases removed.

## 3. Seed list of cases to verify (do not trust until checked)

Candidates from memory and the studies above. Each is a hypothesis to check against dump timestamps and prices, not a fact:

- GameStop and the r/wallstreetbets thread history (pre- and post-January 2021).
- Other 2020 to 2021 retail runs (AMC, BB, SNDL, Dogecoin and similar) as hard examples. Most are attention events, which makes them useful as confound and negative-risk cases.
- Earlier DD-style posts about companies that later ran up, such as semiconductors, EV, and AI names in 2018 to 2020. The Bradley sample is the right place to find these; check whether the authors released a list (unverified).
- AI and developer tooling repos first posted in r/MachineLearning, r/LocalLLaMA, r/programming, or similar that later became companies or acquisition targets. Build from funded-startup lists.

## 4. What makes a post "early and informative" (features to test, not assume)

| Idea | Why it might matter | Data needed |
|---|---|---|
| Low prior mention count of the entity | Early means few earlier mentions | Dump, point-in-time |
| Small market cap and low pre-post volume | Room to move, but also pump risk | Price source |
| Specific, checkable claim (catalyst, number, date) vs hype words | Bradley finding: price-pressure posts lose informativeness | Text features, light NLP |
| Post type: DD with sourcing vs meme or YOLO | Same | Flair, length, link presence |
| Author is not the owner or a known promoter | Self-promotion bias | Author-history features |
| Comment-thread quality (disagreement, corrections by informed users) | May reveal real information | Comments in the dump (scope item in `14`) |
| Cross-source corroboration at T (SEC filing, press release, paper, HN, release notes) | Distinguishes information from noise | Join by entity and date |
| Whether an entity is being discussed in niche subs before general subs | Diffusion path as an early indicator | Cross-sub first-seen times |

Each goes through the registry and ablation process in `14`, and only stays if it improves out-of-time performance.

## 5. Other source types that can generate positives cheaply

These produce candidate unicorns and labels independent of Reddit, and can also act as extra weak-label voters (`04`):

- **Hacker News**: Show HN posts that later reached front page, and the time order versus Reddit.
- **arXiv and papers-with-code**: repos attached to papers that later became widely cited.
- **SEC filings**: S-1s and 8-Ks naming open-source projects, for the company-repo link.
- **Funding and acquisition news**: GDELT or press-release feeds (verify terms and coverage).
- **Package registries**: PyPI and npm download growth as an adoption signal (verify availability).
- **Release notes and job postings**: adoption beyond stars.

Each needs a terms check and a cost estimate before use (`11` rule 5).

## 6. Tiers for the gold set

| Tier | Source | How it is verified | Target count |
|---|---|---|---|
| 1 | Hand-verified positives: lead time known, thesis matches outcome, not confounded | You or me with primary sources | 40 to 60 |
| 2 | Outcome-first positives from section 1, auto-verified timing | Script plus spot checks | A few hundred |
| 3 | Matched negatives and attention-only cases | Script, matched before outcomes | At least equal to tiers 1 and 2 combined |
| 4 | Famous but non-predictive cases (pump-and-dumps, attention spikes) | Hand list | 20 to 30 |

The sealed test slice is drawn before tier 2 is built, from a time period the construction never looked at.

## 7. Practical limits to plan for

- **Liquidity.** A paper return in an illiquid small cap may be unrealizable. Apply the filters in `10` before counting a positive.
- **Hindsight in universe building.** Building from today's tickers and repos drops delisted names and deleted repos. Use point-in-time listings where possible (verify price source coverage).
- **Multiple comparisons.** Every added source or feature is a trial (`12`).
- **Regime changes.** Jan 2021 for WSB, 2023 API and bot-star shifts for Reddit and GitHub. Always show before and after.
- **Not advice.** Phase 2 stays paper-only behind the gates in `10`.

## 8. Proposed stages

| Stage | What | Gate |
|---|---|---|
| U0 | Verify the Bradley sample and any released lists; read primary papers for variable definitions | You skim the summary |
| U1 | Build outcome universes (stocks, tokens, repos), counts only | Counts and cost |
| U2 | Backward search in the dump, earliest mention and lead time | Lead-time histogram |
| U3 | Matched negatives and attention-only controls | Match balance report |
| U4 | Tier 1 hand verification | Your time, about 1 hour per 30 cases |
| U5 | Feed tiers into the label model and gold set | G4 |

## 9. Open items

1. Which domain to start with: tool and repo outcomes (cheap, free) or stocks (price data, stricter gates)? My default is repos first and a stock pass limited to the pre-2021 DD period.
2. Whether comments count as mentions and as sources of positives (`14`).
3. Whether you have preferred seed cases you already know about. They are the fastest way to test the backward search.
