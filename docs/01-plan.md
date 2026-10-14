# 01 - Plan
> **Status: SUPERSEDED in part (October 14, 2026).** The project is now ticker-first, with GitHub-star outcomes deferred, and the study design and decisions in `docs/38-review-decisions.md` and `docs/07-decisions.md` override this document where they differ. Kept for history and for the sections not contradicted.

Scope reframed on October 13, 2026 (second reframe). Supersedes the Reddit-first version.

## Goal

Find early signals in AI, ML, and developer tech (new repos taking off, Hacker News attention) and test whether they precede moves in **finance that is affected by AI, ML, and tech**: public companies, tech and AI ETFs, and crypto tokens with repos. Output calibrated, risk-adjusted probabilities with intervals, and simulate trades on paper only.

We are after early trend indication. We are not claiming a signal causes a price move.

## What changed from the earlier plan

| Before | Now |
|---|---|
| Train on historical Reddit posts | Train on Reddit history from the public 2005 to 2026 repo, joined to GitHub and HN outcomes |
| Reddit post is the unit that gets scored | A **repo or tech event** is the unit. Reddit is an optional daily reader that scores new posts' linked repos with the frozen model |
| Second ThinkPad runs the collector | Gone. **Paid hosting runs all collectors. You develop on your own laptop** |
| Target is "success of a repo" | Two outputs: **tool radar** (repo success) and **finance link** (mapped asset reaction), with the finance link tested first |
| Positives limited by what is on Reddit | Positives come from all of GitHub via GH Archive, so there are far more of them (the real count is still to be measured) |

## The two outputs

1. **Tool radar:** probability that a young repo will be in the top 5% of its cohort on 12-month star gain, using only what is known at scoring time. Feeds your own tools. This works even if the finance link fails.
2. **Finance link:** for repos and events that map to a tradable asset, test whether the early signal precedes abnormal returns, and simulate paper trades. Optional until it passes a kill test (`13`).

## Finance mapping, in short

| Mapping | Example idea | Notes |
|---|---|---|
| Company-owned repo | A repo under a public company's GitHub org grows fast | Materiality matters. A mega-cap barely moves for one repo |
| Token with repo | Crypto token whose project has a repo | Noisy, manipulation-prone, cheapest to test |
| Thematic basket | Aggregate AI repo growth versus semis, software, or AI ETFs | An index test (K3). Diffuse, but a small number of series makes it cheap |
| Displacement | A repo replaces a paid product | Out of scope (needs shorts) |

Honest caveat: I found no evidence that early GitHub growth predicts returns, and the careful retail-attention study I found showed no abnormal returns. Expect a null result and keep the tool radar as the fallback.

## Architecture

```
Laptop (develop, review, run dashboards)
   |  git push / rsync results
   v
Paid VPS (collectors on cron/systemd, DuckDB + Parquet)
   GitHub API / GH Archive  -->  repo features + outcomes
   Hacker News API          -->  attention features + confounder flags
   Prices (Stooq, CoinGecko, FRED) --> returns
   Reddit repo dump (history) + optional daily API read --> posts -> linked repos -> frozen model score
                                      |
                       Label engine --> signal model (regularized logistic regression)
                                      |
              +-----------------------+---------------------------+
              |                                                   |
   Tool radar feed (JSON/report)                  Asset mapper --> Simulator
                                                   |
                                      Truth board (sealed test)   Sandbox
```

The signal model and tool radar do not depend on the asset mapper, simulator, or dashboards. Details: `11` data collection, `12` evaluation and simulation, `13` finance mapping.

## Hosting and budget

- **Everything runs on paid hosting.** Candidate: a Hetzner Cloud CX23 or CAX11 (2 vCPU, 4 GB RAM, 40 GB disk, roughly $7 to $8 a month per the pages I checked, EU prices, US locations about 20% higher). The disk fills fast if raw dumps are stored, so heavy GH Archive work should run as queries or streamed filters, keeping only reduced Parquet (verify the approach before buying, see `11`).
- You develop on your laptop and push code. The server runs scripts only. No LLM agent runs on the server, so there is no surprise token spend there.
- Build budget **$200**, upkeep **$25 per month** (`10`). The $60 phase-1 LLM cap covers the orchestrating agent's own tokens as well (`10`, `11`). Your plan is to use your Claude subscription in Claude Code for the agent work.

## Phases

| # | Phase | Output |
|---|---|---|
| 0 | Repo skeleton, config, spend ledger, kill switch, tests | Working skeleton that spends nothing |
| 0b | Evaluation harness on synthetic data | Leakage tests, permutation tests, planted-signal checks (`12`) |
| 1 | Hosting up, GitHub and HN collectors running | Daily logs of repo activity and HN attention start accumulating |
| 2 | Historical candidate universe from GH Archive | Emerging repos with early curves; real positive rate under 3 definitions |
| 3 | Outcome and confounder labels | Soft labels with confidence, spike flags |
| 4 | K1/K3 kill tests (company repos, tokens, thematic index) | Decides whether the finance link is worth building (`13`) |
| 5 | Baseline model | Regularized logistic regression, rolling-origin validation, decay half-life |
| 6 | Calibration, intervals, gold-set check | Calibrated probabilities, abstention rule, weekly review queue |
| 7 | Dashboards: Truth board and Sandbox | See `12` |
| 8 | Reddit daily reader (optional) | Scores new posts' repos with the frozen model |
| 9 | Watch live predictions for months | Paper only |
| 10 | Markets for real money | Not planned; only after the gates in `10` |

## Funnel and cost control

1. Scripts and SQL filter the candidates. GH Archive does the volume.
2. A Haiku-class model with batch classifies repos by topic and industry (small job).
3. A Sonnet-class model with batch adjudicates a small set (spike checks, gold-set pre-labels).
4. Hard caps per stage and a monthly spend limit in the API console.

## Output

For each flagged repo or event:

- Calibrated probability and an interval
- Top contributing features
- Mapped asset, materiality score, and simulated paper trade, if the finance link has passed
- Abstain when the interval is too wide

Phase 1 delivers a weekly review queue (top 10 to 20) you read and log yes, no, and why.
