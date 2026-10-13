# 19 - Variable catalog (about 60), subreddit scan list, and open-item decisions

Written October 13, 2026 from Eli's requests to restore the wider variable list (stock moves, subs a user frequents, user-type predictions) and to list every subreddit we plan to pull. Each variable is a **candidate**. The registry and ablation process (`14` section 5) decides which survive. "Avail" is when the value is knowable: **T** = post time, **L** = live collector only, **Y** = label side (never a feature).

## Why 60 candidates is fine and 60 features is not

`05`: with roughly 70 to 400 effective positives, a model can carry about N_eff/10 to N_eff/20 features. So:

- Collect all candidates (cheap, and you cannot recompute what you did not store).
- Group them (A to G). Score **groups** by out-of-time ablation first, then variables inside surviving groups.
- Compress dense groups (user subs, text) to a few components fit inside each fold.
- Report importance with intervals, never a single winner list. Correlation findings go in a discovery log as hypotheses until they pass out-of-time.

## A. Post content (14)

| ID | Variable | Avail |
|---|---|---|
| A1 | Links a GitHub repo | T |
| A2 | Contains a cashtag or ticker | T |
| A3 | Company or product name matched (resolver confidence) | T |
| A4 | Post type (DD, question, news link, meme, show-off) | T |
| A5 | Flair | T |
| A6 | Title length | T |
| A7 | Body length | T |
| A8 | "I built / open-sourced / benchmarked" flag | T |
| A9 | Claim specificity (numbers, dates, named catalyst) | T |
| A10 | Hype-word rate (price-pressure language) | T |
| A11 | Sentiment polarity | T |
| A12 | Hedging and uncertainty rate | T |
| A13 | External link domain class (filing, news, blog, paper) | T |
| A14 | Text embedding, 3 to 8 compressed components | T |

## B. Entity at time T (8)

| ID | Variable | Avail |
|---|---|---|
| B1 | Entity kind (stock, token, repo-to-company, repo only) | T |
| B2 | Prior mention count, 30 and 90 days | T |
| B3 | Days since first mention in scanned set | T |
| B4 | Cross-subreddit spread so far | T |
| B5 | Market cap band or repo size band | T |
| B6 | Sector and industry tag | T |
| B7 | Repo age, stars at T, 7-day star growth (company or token repos) | T |
| B8 | Materiality score (`17`) | T |

## C. Market context at T (10)

| ID | Variable | Avail |
|---|---|---|
| C1 | Trailing 5, 21, 63 and 252 day return of the asset (the "yearly stock move" as context) | T |
| C2 | Sector-relative trailing return | T |
| C3 | Trailing volatility | T |
| C4 | Volume ratio versus 30-day average | T |
| C5 | Distance from 52-week high and low | T |
| C6 | Beta | T |
| C7 | Index trend and volatility regime | T |
| C8 | Days to next earnings or known catalyst | T |
| C9 | Short interest (if free data allows, verify) | T |
| C10 | Market open or closed at post time | T |

## D. Subreddit (6)

| ID | Variable | Avail |
|---|---|---|
| D1 | Size and 30/90-day growth | T |
| D2 | Posts per day | T |
| D3 | Shrunk past hit rate (point-in-time) | T |
| D4 | Share of builder or DD posts | T |
| D5 | Removal rate | T (dump caveat) |
| D6 | Regime flag (before or after January 2021, API change dates) | T |

## E. Author and user type (12)

Author ids are hashed. Features are aggregate and behavioral.

| ID | Variable | Avail |
|---|---|---|
| E1 | Account age | T |
| E2 | Prior post count in niche, by bucket (0, 1-2, 3-9, 10+) | T |
| E3 | Shrunk past hit rate (point-in-time, out-of-fold) | T |
| E4 | Subs frequented: top-k subreddit shares | T |
| E5 | Subs frequented: 5 to 10 SVD components of the user x subreddit matrix | T |
| E6 | Activity entropy (specialist versus generalist) | T |
| E7 | Share of activity in finance subs versus developer subs | T |
| E8 | Posting cadence and burstiness | T |
| E9 | Self-promotion history (repeat domain or repo owner match) | T |
| E10 | Author equals repo owner or company-linked | T |
| E11 | Archetype cluster id (below) | T |
| E12 | Karma bucket (expected to be weak) | T |

### User type, done at the archetype level

You asked for predictions of user type, such as profession, so we catch correlations. Plan:

- Build **behavioral archetypes**: cluster users by subreddit mix and activity pattern (for example developer-leaning, trader-leaning, researcher-leaning, hobbyist, promoter). Each cluster is labeled by what it does. That is E11.
- No attempt to state a person's real profession, employer, location, or identity, and no linking across sites (`04` scope rule, kept). A cluster saying "behaves like a developer-heavy member" is enough for correlation work.
- Ids stay hashed, the report never names users, and per-user tables are not exported.
- Correlations are tested at the cluster level, with intervals.

## F. Thread dynamics (6)

| ID | Variable | Avail |
|---|---|---|
| F1 | Score at 1h and 6h | L |
| F2 | Comments at 1h and 6h | L |
| F3 | Upvote ratio | L |
| F4 | Early comment velocity | L |
| F5 | Crossposts at T plus 24h | L |
| F6 | Final score and comment count (dump) | Y, flagged (ingestion-time caveat, `04`) |

## G. Timing and attention context (4)

| ID | Variable | Avail |
|---|---|---|
| G1 | Hour and day of week | T |
| G2 | Holiday or weekend flag | T |
| G3 | Same-week HN or GitHub Trending presence | T |
| G4 | Same-week filing, release, or paper | T |

## H. Outcome and label variables (all Y, never features)

H1 forward abnormal return at 1-20, 21-63, 64-252 days; H2 forward yearly stock move; H3 12-month star gain percentile; H4 lead days; H5 later citation count; H6 post attention effect; H7 confounder flags; H8 placebo percentile; H9 `p`, `c`, `q` factors (`16`).

Total: about 60 candidates plus the label-side fields.

## Handling rules

1. **Each variable is a registry row** with available-at rule, source, version, and compatible set (dump or live).
2. **Missingness is information:** keep an explicit missing flag, and never impute from the future.
3. **Multiple testing:** the correlation sweep over 50+ variables is a trial family (`12`). Adjust with false discovery rate control and keep a sealed slice.
4. **Stratified reports:** every headline number also appears by archetype, subreddit size band, and regime.
5. **Sparse groups:** under about 70% non-missing, the group stays out of the model and in the discovery log.

## Subreddit scan list

Nothing below was pulled. **Verified** means it appeared in the Arctic Shift subreddit API snapshot of February 2025 (`09`). **Unverified** means it is a candidate from my knowledge and must be checked in that API for existence, size, and completeness before pulling. Selection is by the criteria in `11` S1, and every sub gets an `added_at` tag (`14`).

### 1. AI and developer tooling (already verified, `09`)

r/ollama, r/LLMDevs, r/LocalLLM, r/mcp, r/Rag, r/AI_Agents, r/LangChain, r/OpenWebUI, r/coolgithubprojects, r/LocalLLaMA, r/opensource, r/selfhosted.

### 2. Markets (verified, `09`)

r/wallstreetbets, r/Superstonk, r/pennystocks, r/CryptoMoonShots, r/algotrading.

### 3. Candidates to verify: financial

| Group | Subreddits |
|---|---|
| General stock discussion | r/stocks, r/investing, r/StockMarket, r/options, r/thetagang, r/Daytrading, r/RobinHood, r/dividends |
| Research and value | r/SecurityAnalysis (lookup failed earlier), r/ValueInvesting, r/Stock_Picks, r/stockpicks, r/EducatedInvesting, r/investing_discussion |
| Small cap and speculative | r/smallcapstocks, r/UndervaluedStonks, r/weedstocks, r/SPACs, r/RobinHoodPennyStocks, r/UraniumSqueeze |
| Biotech and pharma | r/biotech, r/BiotechStocks |
| Crypto | r/CryptoCurrency, r/CryptoMarkets, r/Bitcoin, r/ethtrader, r/ethfinance, r/SatoshiStreetBets, r/defi, r/altcoin |
| Macro and misc | r/thewallstreet, r/Vitards, r/economy, r/FinancialCareers (noise control) |

### 4. Candidates to verify: tech, company, and science

| Group | Subreddits |
|---|---|
| AI and ML | r/MachineLearning, r/artificial, r/singularity, r/OpenAI, r/ClaudeAI, r/ChatGPTCoding, r/StableDiffusion, r/learnmachinelearning, r/datascience, r/deeplearning |
| Dev and infra | r/programming, r/webdev, r/Python, r/rust, r/golang, r/devops, r/kubernetes, r/docker, r/commandline, r/neovim, r/homelab, r/linux, r/github |
| Startups and products | r/startups, r/SaaS, r/SideProject, r/indiehackers, r/Entrepreneur, r/venturecapital, r/ProductHunt, r/hackernews |
| Security | r/netsec, r/cybersecurity |
| Company-specific investor subs | r/AMD_Stock, r/NVDA_Stock, r/teslainvestorsclub, r/PLTR (confirm exact name), r/RKLB (confirm exact name) |
| Hardware and frontier tech | r/hardware, r/QuantumComputing, r/robotics, r/spacex, r/batteries, r/energy, r/Futurology |

### 5. Controls and negatives

r/personalfinance and r/FinancialCareers (off-topic money talk, to check the model does not fire on generic finance language), promotional-heavy subs already listed (r/pennystocks, r/CryptoMoonShots), and a small random sample of unrelated large subs to estimate base rates of GitHub and ticker mentions.

### How the list grows

Run the Tier C expansion in `09`: user-overlap and crosspost graphs, then rank neighbors by share of mentions that resolve to a ticker or repo and by prior positive rate **computed only from earlier years**. The point is finding small communities where the first mention of something that later moved appeared. Large subs give volume. Small subs give first mentions, so both are scanned, and cross-sub first-seen time is a variable (B4).

## Decisions on the open items from `17` and `18`

| Item | Decision | Reason |
|---|---|---|
| Local disk | All data work happens off-laptop (cloud). Laptop keeps code, docs, and under about 1 GB of Parquet. Data lives outside the Dropbox folder (`data/` is already in `.gitignore`) | 3 GB free cannot hold more, and Dropbox must not sync data |
| Cloud | Short-lived Hetzner-style VM plus object storage for reduced Parquet. Spend cap $60 for the ingest within the $200 build budget. Requires your approval before purchase | Cheapest fit |
| Benchmark | Market index plus sector ETF | Cheap, interpretable, upgrade only if results justify it |
| Report cadence and delivery | Weekly, Markdown file in `reports/`, plus a one-paragraph email draft you approve | Matches the weekly review queue (`01`) |
| Payoff scenario | G = L = 100%, `p*` = 0.70 | Existing default in `07` and `10` |
| Multi-entity posts | Prominence-weighted mean `p`, per-entity rows kept for diagnostics | `16` default |
| Comments | Posts first, comments as a later extension | Size and cost |
| Type C posts | Excluded from training, kept for coverage reporting | Avoids teaching "has a link" |
| Subreddit scope | Lists above, verified in the API first, then expanded by link frequency with `added_at` | Controls bias (`14`) |
| First domain | Repos and tool outcomes plus the pre-2021 stock DD period | `15` default |

Purchases and downloads still wait for your go-ahead.
