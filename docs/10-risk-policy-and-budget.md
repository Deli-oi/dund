# 10 - Risk policy and budget

This is a research design, not investment advice. No real money is planned for a long while.

## Where these numbers come from

The risk rules below are conventional quant and risk-management rules of thumb, recalled from background knowledge: Kelly sizing with a fractional multiplier, small per-position risk, Sharpe hurdles, a stricter significance bar for discovered strategies, and tiered drawdown limits. Real fund parameters are not public, so treat these as sensible defaults to be tuned after testing, not industry-verified values. The calculations are mine (a script run this session), and the assumptions are labeled.

Papers behind the multiple-testing rules (titles verified, details not re-read):

- Harvey, Liu and Zhu, "... and the Cross-Section of Expected Returns" (NBER w20592). Argues for a higher significance bar (a t-statistic around 3) once many strategies have been tried.
- Bailey and Lopez de Prado, "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality" (SSRN 2460551).

## Two policies, because errors cost different things

### A. Time and education policy (phase 1, GitHub outcomes)

A false positive costs reading time, not money. So:

- Show a **weekly review queue** of the top k (start with 10-20) posts, ranked by calibrated probability, each with its interval.
- Abstain when the interval is too wide to be useful.
- No hard probability cutoff is needed. The review budget (k per week) is the cutoff.
- Still judge the model on precision at top k and calibration.

### B. Money policy (phase 2, markets; inactive for now)

A false positive can cost real capital, so the rules are strict.

#### 1. Breakeven precision

Break-even precision is `p* = loss / (loss + gain)`. A scenario table (G = gain on a hit, L = loss on a miss, as fractions of the position):

| G | L | b = G/L | Breakeven p* | p* + 0.15 | p* + 0.20 |
|---|---|---|---|---|---|
| 0.5 | 1.0 | 0.50 | 0.667 | 0.817 | 0.867 |
| 1.0 | 1.0 | 1.00 | 0.500 | 0.650 | 0.700 |
| 2.0 | 1.0 | 2.00 | 0.333 | 0.483 | 0.533 |
| 3.0 | 1.0 | 3.00 | 0.250 | 0.400 | 0.450 |
| 1.0 | 0.5 | 2.00 | 0.333 | 0.483 | 0.533 |

**Default scenario: G = L = 100% of the position** (a hit doubles, a miss can be a total loss, which is a realistic worry for illiquid small caps and crypto). That gives p* = 0.50.

**Default rule: act only if the lower confidence bound on precision is at least p* + 0.20 = 0.70.**

#### 2. How many alerts that takes (Clopper-Pearson lower bound)

Hits out of alerts needed so the one-sided lower bound reaches the target, if observed precision is about what is shown:

| Target lower bound | Observed precision | At 90% confidence | At 95% confidence |
|---|---|---|---|
| 0.65 | 0.90 | 9 of 10 | 11 of 12 |
| 0.65 | 1.00 | 6 of 6 | 7 of 7 |
| 0.70 | 0.85 | 14 of 16 | 24 of 28 |
| 0.70 | 0.90 | 11 of 12 | 13 of 14 |
| 0.70 | 1.00 | 7 of 7 | 9 of 9 |
| 0.80 | 0.90 | 29 of 32 | 40 of 44 |
| 0.80 | 1.00 | 11 of 11 | 14 of 14 |

Caveat: these counts assume independent alerts. Alerts in the same week, theme, or market regime are correlated, so **count independent episodes, not alerts** (cluster by week and theme).

#### 3. Evidence for the whole strategy

- **Trying many variants inflates luck.** The expected best result from N variants with no real skill is about 1.6 standard errors at N=10, 2.0 at N=25, 2.3 at N=50, 2.5 at N=100, and 3.1 at N=500. So **log every configuration tried** and demand more than the luck level.
- **Significance bar:** aim for a t-statistic of about 3 (not 2) for any claim that the strategy works, after accounting for the number of variants tried.
- **Live track records are slow.** With independent bets of equal size, G = L, and precision 0.70, the annualized Sharpe is about 1.07 at 6 alerts a year, 1.51 at 12, 2.18 at 25, and 3.09 at 50. But proving a Sharpe statistically takes years (rough iid approximation, which understates the time when returns are skewed):

| True annual Sharpe | Years to reach t >= 2 | Years to reach t >= 3 |
|---|---|---|
| 0.5 | 18.0 | 40.5 |
| 1.0 | 6.0 | 13.5 |
| 1.5 | 3.8 | 8.5 |
| 2.0 | 3.0 | 6.8 |
| 3.0 | 2.4 | 5.5 |

Consequence: months of paper-trading can reveal a broken model but cannot prove a good one. Judge live results by precision and calibration, not by Sharpe, and keep real money out for a long while.

#### 4. Position sizing and drawdown (for paper trading first)

A Monte Carlo simulation assumed 50 alerts a year for 2 years, G = L = 100% of the position, and true precision drawn from the posterior of a 42-of-60 backtest. The stressed case subtracts 0.10 from precision to mimic live decay.

| Size per alert | Stress | P(drawdown > 10%) | P(> 15%) | P(> 25%) | 5th percentile end value | Median end value |
|---|---|---|---|---|---|---|
| 0.5% | none | 0.000 | 0.000 | 0.000 | 1.071 | 1.220 |
| 0.5% | -0.10 | 0.014 | 0.001 | 0.000 | 0.969 | 1.104 |
| 1% | none | 0.014 | 0.001 | 0.000 | 1.145 | 1.484 |
| 1% | -0.10 | 0.142 | 0.039 | 0.002 | 0.937 | 1.191 |
| 2% | none | 0.199 | 0.057 | 0.003 | 1.297 | 2.182 |
| 2% | -0.10 | 0.576 | 0.308 | 0.066 | 0.835 | 1.462 |
| 5% | none | 0.922 | 0.632 | 0.198 | 1.778 | 6.531 |
| 5% | -0.10 | 0.994 | 0.920 | 0.581 | 0.591 | 2.172 |

These are illustrative: the 42-of-60 backtest is invented for the simulation.

**Default sizing:** at most 1% of capital per alert, at most a quarter of the Kelly fraction (whichever is smaller), and the whole experiment limited to a small sleeve you could lose entirely (5% of investable assets is a common placeholder).

**Drawdown tiers (placeholders to tune):** review at 5%, cut position sizes in half at 10%, stop and re-audit at 15% to 20%.

#### 5. Gates before any money

1. **Research gate:** rolling-origin test shows the lower bound on precision at or above target on enough independent episodes, beats simple baselines, and is calibrated.
2. **Live gate:** at least 12 months of live logging, with enough resolved alerts to clear the table in section 2 and no calibration drift.
3. **Money gate:** start at 0.5% per alert, scale to 1% only after the first two gates and a check for the number of variants tried.

## Budget

Given: **$200 build budget, $25 per month upkeep.** All figures below are planning estimates with stated assumptions.

### Prices used (Claude API pricing page, per million tokens)

| Model | Input | Output | Batch input | Batch output |
|---|---|---|---|---|
| Haiku 5.5 (prompts up to 100k tokens) | $0.10 | $0.50 | $0.05 | $0.25 |
| Sonnet 5.5 | $2 | $10 | $1 | $5 |
| Opus 5.5 | $4 | $20 | $2 | $10 |

Batch is 50% off. Check the pricing page again before committing.

### LLM cost estimate, phase 1

Assumptions: about 894,000 posts in the seed set now (559,000 in Feb 2025 times an assumed 1.6), a keyword filter that passes 20% of posts, 500 input and 80 output tokens per extraction, and 3,000 adjudication items at 3,000 input and 600 output tokens.

| Step | Cost |
|---|---|
| Bulk extraction on filtered posts, Haiku batch | about $8 (range $4 at a 10% filter to $14 at 35%) |
| Same on Haiku without batch | about $16 |
| Adjudication, Sonnet batch | $18 |
| Adjudication, Sonnet without batch | $36 |
| **Rough phase-1 total** (Haiku batch plus Sonnet batch) | **about $26** |
| Mistake case: all posts, Sonnet, no filter | about $1,600 |

The last row is why the filter and a spending cap matter more than model choice. Set a monthly spend limit in the API console (check the current option).

### Revised phase-1 LLM allocation (supersedes the table above for planning)

The estimate above assumed name-based extraction over about 179,000 posts and left out the orchestrating agent's own tokens. The POC is now link-only (`11`), so bulk extraction mostly disappears and the agent's own cost becomes the main line.

| Line | Estimate | Cap |
|---|---|---|
| Repo topic and industry classification, 5,000 repos, Haiku batch | $0.50 | |
| Gold-set pre-labeling, 300 posts, Sonnet batch | $1.35 | |
| Spike and confound adjudication, 1,000 items, Sonnet batch | $6.00 | |
| Weekly report text, top 20 a week for a year, Sonnet batch | $3.64 | |
| **Data tasks total** | **$11.49** | **$15** |
| Orchestrating agent, 150 turns, 30k context, mostly cached | $3.33 | |
| Orchestrating agent, 300 turns, 40k context, mostly cached | $8.58 | |
| Orchestrating agent, 300 turns, 40k context, uncached | $28.50 | |
| Orchestrating agent, 600 turns, 50k context, uncached | $69.00 | **$35** |
| Reserve | | $10 |

Assumptions: token counts per task as in the cost scripts, Sonnet 5.5 at $2 input and $10 output per million tokens, cache reads at $0.10, and "mostly cached" meaning 90% of input tokens read from cache. The orchestration figures depend on how long the agent loops, so checkpoints and short scripted stages matter more than model choice. A 600-turn uncached run would exceed the whole $60.

### Build budget plan ($200)

| Item | Amount |
|---|---|
| LLM spend cap, phase 1 | $60 |
| Collector hosting, 3 months prepaid | about $20 |
| External SSD, only if laptop space is short | up to $90 (rough guess, check price) |
| Reserve | $30 |

If no SSD is needed, the unspent amount stays in reserve.

### Upkeep budget ($25 per month)

| Item | Amount |
|---|---|
| Collector VPS | about $6-7 (EUR 5.49-5.99) |
| Live LLM scoring and adjudication | about $1-5 (assumes about 17,000 new posts a month, 20% passing the filter) |
| Data and APIs (GitHub, GH Archive, Stooq, GDELT, Reddit OAuth) | $0 on free tiers |
| Headroom | about $13 or more |

VPS prices are from one article about Hetzner's June 2026 repricing, excluding IPv4: CX23 EUR 5.49, CAX11 EUR 5.99 per month. The dollar figure assumes a rough exchange rate. Verify before buying.

### Time costs that are not dollars

- Pulling GitHub star history through the API at 5,000 requests per hour: about 4 hours for 2,000 repos at roughly 10 pages each, 20 hours for 5,000 repos at 20 pages, 60 hours for 10,000 repos at 30 pages. Free, but slow.
- Embedding about a million short texts on laptop CPU: hours, not benchmarked on your machine.

### Verdict

The budget works for phase 1 as long as the keyword filter and the spending cap are in place. It does not leave room for paid datasets such as CRSP (check whether your school library gives access instead).
