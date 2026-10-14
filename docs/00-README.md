# dund: early-signal Reddit model

An experiment to find early signals in small Reddit communities: posts that came before something later took off, so a model can learn to flag similar new posts.

This is a research project, not investment advice. No personal money goes into it for a long while (see `07-decisions.md` and `10-risk-policy-and-budget.md`).

> Reading order (D14): `07, 38, 24, 32, 28, 31, 25, 27, 37`.

## One-paragraph summary

Test whether posts in 14 finance-related subreddits, pulled as a full census from Arctic Shift (2012 to 2026), contain early signals about tickers. The unit is the ticker-day; stage 1 uses posts only, and price enters only through labels. The primary claim is that flagged ticker-days have a net abnormal return (10 days, after cost) whose lower bound exceeds matched controls. Live scoring uses the same conversion path as training. Research only, not investment advice. GitHub outcomes are deferred. Older docs describing the repo-first plan are kept as history.

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
| `27-source-census-and-deleted-data.md` | Measured access and volume for other sources; whether removed Reddit bodies can be recovered (they cannot) |
| `28-sample-size-levers.md` | Measured levers for raising sample size: ticker-days as the unit, comments, years, subs, projections |
| `29-price-sources.md` | Free historical price sources probed, coverage and misses |
| `30-gharchive-feasibility.md` | GH Archive and GitHub API feasibility (deferred track) |
| `31-synthetic-power-results.md` | Synthetic power results (flag vs base rate check) |
| `32-preregistration-draft.md` | Pre-registration v2 draft, not frozen |
| `33-resolver-tuning.md` | Entity resolver tuning on real census posts |
| `34-price-pull.md` | Yahoo chart price pull: how to run, misses |
| `35-label-builder.md` | Label builder implementing the hit rule |
| `36-ticker-day-counts.md` | Ticker-day counts (partial run) |
| `37-label-and-evaluation-note.md` | Plain-language label and evaluation summary |
| `38-review-decisions.md` | Review decisions D1 to D15 (authoritative) |

## Reading order

`07, 38, 24, 32, 28, 31, 25, 27, 37` (D14). Then the rest as needed.

## Status

Census running, code and docs built, no outcome data joined, no signal tested. Docs `01` to `23` describe the earlier repo-first framing and are history where they disagree with `07` and `38`.
