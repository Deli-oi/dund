# 24 - Hypothesis and study design

> **Status (October 14, 2026): updated by `38` (decisions D1 to D11) and `32` version 2.** The hurdle H = 0.70 on precision is retired as a pass/fail bar. The primary claim is now the expected net abnormal return of flagged ticker-days minus matched controls, with a two-way clustered bootstrap lower bound above zero. Precision and hit rate are descriptive; the live threshold is a data-derived break-even precision. Where the text below says "hit rate lower bound exceeds H", read it through `32` v2.

October 13, 2026. Eli's framing: this is as much a research paper as an algorithm. We are testing a hypothesis, and we do not know in advance how much data a working model would need. This document makes that explicit and is the top-level frame for the other docs.

## The hypothesis

> **H1.** There exists a **signal set** `S`, computed from posts in a **source universe** `U`, that produces an **early call** `C` such that, out of time and net of costs, the lower bound of its hit rate at **confidence level** `L` exceeds the **hurdle** `H` and beats the stated baselines.

| Name | Short | Meaning in this project | Where it lives |
|---|---|---|---|
| Signal set | `S` | Variables derived from the post, author, subreddit, entity, and market context | `19` |
| Source universe | `U` | Which subreddits, entity kinds (stock, token, repo-to-company), and years we draw from | `20`, `22` |
| Early call | `C` | Output: calibrated probability, interval, and action with margin over the hurdle | `18` |
| Confidence level | `L` | Coverage of the interval, for example 95% | `04`, `18` |
| Hurdle | `H` | Originally breakeven plus safety margin (0.70). Retired as a bar (`38` D1); now the net-edge-above-zero criterion and a data-derived break-even precision | `07`, `10`, `32` |

**Null H0:** no (`S`, `U`) does better than the baselines (asset's own trailing return, repo-only features, base rate) once the search is accounted for.

## Two things that must both hold

1. **Predictive claim (reworded per `38` D1):** the net abnormal-return difference of flagged ticker-days versus matched controls has a one-sided lower bound above zero on sealed data. Precision is reported descriptively against the break-even precision, not against 0.70.
2. **Profit claim:** simulated paper positions on those flags earn a net return above benchmark after costs and slippage, with a lower bound above zero and drawdown inside `10`. A good hit rate with a bad payoff does not count.

Precision alone is not a profit indicator, so the second claim is separate and reported separately.

## Why "exists a signal set in a universe" is dangerous, and the protection

Searching many (`S`, `U`) choices until one works is the standard way to fool ourselves. So:

- **Three phases with different rules.**
  1. **Exploratory:** free search over `S` and `U` on training and validation periods. Every try is logged and counted (`12` trial counter). Output: candidate specifications, no claims.
  2. **Confirmatory:** one frozen specification (`S`, `U`, `C`, `L`, `H`, metric, stopping rule) written down before touching the sealed period, evaluated once.
  3. **Replication:** the frozen model scored forward in time on data that did not exist at freezing (live collector, paper only).
- **Adjusted evidence.** The exploratory trial count enters the confirmatory test as a penalty (deflated or adjusted significance, `12`), so a best-of-many result must clear a higher bar.
- **Sealed data touched once.** If the confirmatory test fails, the spec is not retuned on the same data.

## Data need is an output of the study

We do not know the data needed, because it depends on the true effect size (`23`). So the design is sequential:

1. **Pilot** (R0 and a broad uniform sample) measures resolution rate, base rate, variance, and clustering.
2. **Learning curve:** fit performance versus data size on the pilot to extrapolate whether the effect is reachable.
3. **Increments:** pull more only while the projected interval can still separate the effect from `H`. Stopping rules are written before the run.
4. **Verdict categories:**

| Verdict | Condition |
|---|---|
| **Supported** | Confirmatory lower bound above `H` and baselines, profit claim holds, replication does not contradict |
| **Not supported** | Interval is tight and below `H` or baselines at the data available |
| **Underpowered** | Interval too wide to decide and projected data cannot narrow it. Reported as such, never as a pass |

All three are valid results. The paper-style output is the same in each case: what we tried, what we saw, what we could not tell.

## What the study reports regardless of outcome

- Data description and representativeness checks (`22`).
- Every variable tested and how many trials (`19`, `12`).
- Baselines and effect sizes with intervals, by sub, entity type, period, and archetype.
- Negative controls and placebo tests (`13`).
- The power analysis and the data actually obtained (`23`).
- Limitations: free price data coverage, survivorship, regime changes.

## Relationship to the other documents

| Doc | Role under this frame |
|---|---|
| `14`, `22` | Data collection and representativeness: the measurement instrument |
| `15` | Where candidate `S` variables come from (discovery only) |
| `16`, `17` | Label construction and weighting: part of the exploratory design, versioned |
| `18` | The output `C` and its margin over `H` |
| `20` | Order of the first look at `U` |
| `23` | Power and stopping |
| `10`, `12`, `13` | Risk gates, evaluation suite, kill tests |

Not investment advice, paper only.
