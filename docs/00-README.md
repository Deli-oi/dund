# dund: early-signal Reddit model

An experiment to find early signals in small Reddit communities: posts that came before something later took off, so a model can learn to flag similar new posts.

This is a research project, not investment advice. No personal money goes into it for a long while (see `07-decisions.md` and `10-risk-policy-and-budget.md`).

## One-paragraph summary

Mine historical Reddit for posts that mention something checkable. Phase 1 uses AI and developer tooling subreddits and GitHub repos, because outcomes are objective, free, and quick to resolve. For each mention, look up what happened afterward using outside data, and combine several noisy signals into a soft label. Train a regularized logistic regression on information that existed at posting time only, using older years for training and newer years for testing, with time-decay weights. Output a calibrated probability with an interval, and abstain when unsure. False positives are expensive, false negatives are fine. We are looking for trends in early indication, not claiming posts cause outcomes. Two tracks share one engine: GitHub tooling (primary) and crypto tokens with repos (a cheap kill test of the profit link). Stocks and options come later, behind stricter risk gates. If the profit link fails, the model still works as a tool radar for your own tools. Budget: $200 to build and $25 per month.

## Files

| File | What's in it |
|---|---|
| `01-plan.md` | Goal, scope, phases, budget summary, funnel and cost control |
| `02-tools-and-applications.md` | Tools by stage and what each is for |
| `03-data-sources.md` | Reddit data (historical and live), verified findings, outcome data, event data |
| `04-techniques.md` | Labels, weak supervision, features, time handling, risk adjustment, calibration |
| `05-sample-size-and-evaluation.md` | The d vs N math, test sizing, metrics |
| `06-risks-and-pitfalls.md` | Biases and ways this could fool us |
| `07-decisions.md` | What has been decided so far |
| `08-open-questions.md` | Answered questions, what still needs your input, hardware options |
| `09-seed-subreddits.md` | The seed subreddit list, how it was verified, discovery plan |
| `10-risk-policy-and-budget.md` | Risk cutoffs, drawdown and sizing numbers, gates, cost model, revised $60 allocation |
| `11-data-collection-runbook.md` | Agent rules, subreddit selection criteria, pull stages S0-S9, gates, stop conditions |
| `12-evaluation-and-simulation-suite.md` | Test suite, Truth board vs Sandbox dashboards, simulator, sort keys |
| `13-signal-to-asset-mapping.md` | How a repo signal might map to a tradable asset, evidence, kill tests, tool-radar fallback |
| `14-data-collection-deep-dive.md` | Audit of the data plan for the Reddit-history scope, leakage issues, adjustable-input design, revised stage order |
| `15-finding-high-value-positives.md` | Outcome-first search for strong positive cases, survivorship controls, gold-set tiers, literature on Reddit signals |
| `16-post-first-data-model.md` | Post as the input row, entity outcomes attached, impact score and per-row confidence |
| `17-market-target-weighting.md` | Market-shift standard, voter weights, per-example weights, and the Arctic Shift data source |
| `18-compute-and-report-output.md` | Laptop-first compute with cloud overflow, laptop disk limits, and the margin-over-threshold report |
| `19-variable-catalog.md` | About 60 candidate variables, user archetypes, subreddit scan list, open-item decisions |
| `20-subreddit-prioritization.md` | Scored ranking of the 86 candidate subs, waves, data-need math, override rules |
| `21-cost-estimate.md` | Total build and recurring cost ranges, cost drivers |
| `22-representativeness-and-sampling.md` | Census pull rules, skew sources, train-versus-live checks, reweighting |
| `23-data-need-reassessment.md` | Power math, revised data need, explore-first plan, kill criteria |
| `24-hypothesis-and-study-design.md` | The hypothesis (signal set S in universe U gives early call C at confidence L over hurdle H), phases, verdicts |
| `25-r0-pilot-findings.md` | First real data: one-month census of 14 subs, volumes, removal, cashtag and repo-link findings |
| `26-other-sources.md` | Other forums and sources beyond Reddit (candidates, scoring priors, first set, verification plan) |

## Reading order

`07-decisions.md`, then `01-plan.md`, then `11-data-collection-runbook.md`, then `08-open-questions.md` (the "Needs your input" section), then the rest as needed.

## Status

**Data source:** the public git repo of Reddit data covering 2005 to 2026. See `11`.

Planning only (data collection runbook, evaluation suite, and profit-link plan now written). Nothing has been downloaded or built yet. Numbers marked as assumptions in `05` and `10` are planning estimates, not measurements. Items marked "verified" in `03` and `09` were checked against live sources on October 13, 2026.
