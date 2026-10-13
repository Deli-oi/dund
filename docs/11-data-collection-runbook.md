# 11 - Data collection runbook (agent-ready)

Rewritten October 13, 2026 for the reframed scope (`01`). Thresholds marked (placeholder) are starting guesses to tune after the first counts. Nothing here has been run yet. Items marked (verify) were not confirmed.

## Where things run

> Updated October 13, 2026: laptop-first with cloud overflow. See `18`. The VPS description below is the earlier default.

- **Laptop:** development, Claude Code, review, dashboards.
- **Paid VPS:** all scheduled collectors and the warehouse. Scripts only, no LLM agent on the server.
- **Heavy bulk work:** GH Archive history is large. Prefer running filters as queries (Google BigQuery's public GH Archive dataset, free monthly query allowance, verify) or streaming hourly files and keeping only reduced Parquet. Do not store raw dumps on a 40 GB disk.

## Rules for the agent

1. **Scripts do the volume, the LLM does only judgment.**
2. **Reduce early.** Filter before storing. Never download what you can query.
3. **Resumable and logged.** Every stage writes checkpoints and logs.
4. **Hard caps.** Every stage has a spend, request, disk, and time cap. `ledger.jsonl` is updated on every paid call. The agent stops at a cap.
5. **No workarounds.** If a source blocks a request or its terms forbid something, stop and report. Do not circumvent limits, mask identity, or scrape rendered pages.
6. **No trading, no publishing.** Paper only. Never publish usernames.
7. **Human gates.** Pause at each gate and wait.
8. **Secrets** live in a `.env` on each machine, never in the repo or logs.

## Source rules (read these)

| Source | Rule I found | Plan |
|---|---|---|
| **Reddit** | Historical posts come from the public 2005 to 2026 dump repo (see below). Live API use is optional | Used for training, labels and features, filtered to the seed subreddits |
| **Hacker News** | The official Firebase API page states no terms and "currently no rate limit." Y Combinator's site Terms bar "data mining, robots, scraping or similar" and bar circumventing blocks, but also refer to "means intentionally made available." Neither document bans AI training | Use only the official API (and the Algolia search service, terms unchecked, verify). Low request rate, descriptive User-Agent, stop on any block. The terms are ambiguous, so this is your risk call |
| **GitHub** | API token, 5,000 requests per hour (verify). Terms of GitHub API and GH Archive licensing not re-read | Use the API with a token for current state and the star-with-timestamp media type where needed (verify). Use GH Archive for history |
| **Prices** | Stooq, CoinGecko, FRED. Terms not read | Check each site's terms before heavy use (verify) |

### Reddit historical data

Decision (October 13, 2026): use the public git repo of Reddit data covering 2005 to 2026 as the training source.

- Stream and filter to the seed subreddits in `09` and to posts that link or name a GitHub repo. Keep only reduced Parquet, not raw dumps (VPS disk is 40 GB).
- Record the repo URL, commit or release, and file checksums in the spend and data ledger.
- Live API access (free OAuth, 100 queries per minute, verify) is optional, for a daily read of new posts scored by the frozen model.
- Seed subreddits are in `09`.

## Budget for the $60 LLM cap

| Line | Estimate | Cap |
|---|---|---|
| Data-task LLM calls (repo classification, gold-set pre-labels, spike adjudication, weekly report text) | about $11.50 (re-estimate after repo counts) | $15 |
| Orchestrating agent's own tokens | $3 to $29 for 150 to 300 turns, up to $69 for 600 uncached turns. On your subscription this is $0 in credits but subject to usage limits (unverified) | $35 |
| Reserve | | $10 |

## Stages

### S0. Skeleton and guardrails

- Repo skeleton, config with caps, `ledger.jsonl`, a `KILL` file check before every paid call or big request, tests. (A starter is in the handoff repo.)
- Provision the VPS, create a non-root user, firewall, `.env`. Create a GitHub token.
- Output: dry run that spends nothing.

### S1. Candidate universe (GH Archive)

- **Method:** query GH Archive events (WatchEvent, CreateEvent, ForkEvent, PushEvent, etc.) to find repos first seen in a window (for example 2021 onward), with repo age at first star of 365 days or less. Keep only reduced tables (repo id, name, created, per-day star and fork counts for the first 365 days, owner type).
- **Filters (placeholders):** non-fork, at least 5 stars within 30 days (removes dead repos), exclude archives and obvious spam or bot-star patterns (flag, do not delete).
- **Sizing first:** count candidates and query cost on one month before running the full range. Stop if cost exceeds the cap.
- **Cohorts:** by month of first star. **Output:** candidate table and cohort sizes.
- **Gate G1:** you approve counts and cost.

### S2. Early curves and outcomes

- From the same reduced tables: stars at 3, 7, 14, 30 days (features) and at 90, 180, 365 days (labels), forks, contributors, releases when available.
- **Time rule:** features use data up to scoring time T only. Labels use data after T. Test that no label field leaks into a feature (`12`).
- Fill gaps for current repos with the GitHub API (requests capped, G3).
- **Gate G3:** GitHub request budget.

### S3. Hacker News attention

- For each candidate repo URL: front-page or Show HN posts, points and comments at 24 hours, post date. Use the official API or Algolia sparingly (verify endpoint).
- Flag a repo spike-confounded when growth is dominated by one day and the HN post came before it.
- Output: HN features and confounder flags.

### S4. Labels

- Within each first-star-month cohort (pool adjacent months below 30 repos), compute 12-month star-gain percentile. Success = top 5% (variants top 1% and 10%). Right-censored repos are unknown, not negatives.
- Label model: weighted voting of 12-month percentile, 3-month growth, activity at 12 months, confounder flag. Own implementation.
- **Gate G4:** leakage tests pass and the label distribution looks sane.

### S5. Classification and org mapping (small LLM job plus curation)

- Haiku-class batch to tag each repo by topic and industry (about $0.50 per 5,000 repos).
- Build the **org-to-ticker table** for the finance link: seed list of public companies with notable open-source orgs, curated by hand, then check each name against SEC company data (EDGAR) (verify). Record market cap band and an AI/ML/tech exposure tag.
- Token-to-repo map from CoinGecko metadata (verify).

### S6. Gold set

- Around 150 repos: verified hits, matched non-hits chosen before looking at outcomes, spike-confounded cases, self-promotional duds. A Sonnet-class batch pre-labels with a rationale.
- **Your time: about 1 hour.** Sort items by model uncertainty and by disagreement between two labeling passes. You judge the 60 to 80 most uncertain at under a minute each. The rest stay LLM-labeled at lower weight. The sealed 40% is hand-labeled first. Fewer hand labels means wider intervals, and we report that.

### S7. Live collectors (phase 1, start early)

- Daily jobs on the VPS: new-repo star curves from the GitHub API for the tracked universe, HN front page and Show HN, daily prices for mapped assets. Fixed-age snapshots so features at scoring time are reproducible.
- Output: appended Parquet partitions, a daily health log, disk check.

### S8. Finance kill tests (see `13`)

- K1: company-owned repos and token repos, event study with placebo dates.
- K3: aggregate AI repo-growth index versus tech and AI ETFs.
- Spend: $0 in model calls.

### S9. Reddit daily reader

- Optional live read. See above.

## Human approval gates

| Gate | After | You decide |
|---|---|---|
| G1 | S1 | Candidate counts and query cost |
| G2 | S1 | Whether raw positives are enough (stop and rethink if the top-5% definition gives fewer than about 300) |
| G3 | before large GitHub API pulls | The GitHub request budget |
| G4 | S4 | Labels sane and leakage tests pass |
| G5 | S8 | Whether the finance link survived the kill tests |
| Spend | any stage | Pause at 80% of any cap and ask |

## Stop conditions

- Any cap reached, `KILL` present, or three consecutive failures of the same request type.
- A source returns a block or a terms warning (stop and report).
- Disk above 80% on the VPS.

## Folder layout (data, kept out of git)

```
dund-data/
  parquet/        reduced tables (candidates, curves, outcomes, hn, prices)
  warehouse.duckdb
  gold/           labeled sets (sealed part kept separate)
  logs/  ledger.jsonl  KILL
```

## Open items

- Which VPS to buy and where (US vs EU price), and whether 40 GB suffices or a volume is needed (verify).
- Whether GH Archive via BigQuery fits free limits for the chosen range (verify).
- Hacker News terms: the call is yours (see source rules).
