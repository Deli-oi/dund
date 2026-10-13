# 08 - Open questions

Updated after a round where Claude answered what it could. Defaults are Claude's choices and can be overridden. Numbering follows the earlier list.

## Resolved this round

| # | Question | Answer | Where |
|---|---|---|---|
| 1 | Which domain first? | **Updated.** Two tracks on one engine. Track A (AI and dev tooling, GitHub outcomes) is primary because it can be measured and also feeds your own tools. Track B (crypto tokens with repos) runs as a cheap parallel test. A kill test decides whether any profit module is worth building. The evidence I found does not support a large expected upside in any track | `09`, `13` |
| 2 | Seed subreddits | 9 core, 3 large contrast subs, plus graph expansion to find small ones | `09` |
| 4 | Model-call budget | **Updated.** $60 cap for phase-1 LLM spend within the $200 build budget, now covering both data tasks (about $11.50 estimated, capped at $15) and the orchestrating agent's own tokens (capped at $35, estimated $3 to $29 for a 150 to 300 turn run), with $10 reserve. A few dollars per month upkeep, spend limit in console | `10`, `11` |
| 6 | What counts as a success? | Top 5% of cohort on the primary outcome. Top 1% and 10% compared as variants | `07` |
| 7 | Outcome definition | GitHub: 12-month star gain as a percentile within the first-mention-month cohort, plus 3-month growth, 12-month activity, citations as extra votes. Markets: excess return over benchmark, volatility-scaled, 12 months or more, liquidity filter | `04`, `07` |
| 8 | Horizons | Checkpoints at 3 and 12 months, 24 months as comparison (GitHub). The best one is an experimental result | `04` |
| 9 | Credit rule | First mention only | `07` |
| 10 | Decay half-life | Grid of 1, 2, 3, 4, 6 years chosen on validation folds. Starting guess 3 years | `07` |
| 11 | Risk threshold | Phase 1: weekly top-k review. Phase 2: lower bound on precision at breakeven plus 0.20 (0.70 for the default payoff), 1% max per alert, quarter Kelly cap, drawdown tiers | `10` |
| 12 | What does an alert look like? | Weekly markdown or HTML review report plus a CSV for your judgments | `02` |
| 17 | Arctic Shift freshness | Near-live for some subs, uneven for others (stops between July and October 2026 for many seed subs). Subreddit metadata is a Feb 2025 snapshot. Fresh posts carry ingestion-time scores | `03` |
| 18 | Reddit API limits | Free OAuth: 100 queries per minute per client ID. Unauthenticated traffic is blocked. Descriptive User-Agent required. Deleted content must be removed | `03` |
| 20 | Snorkel | Not relied on. Write our own small label model | `02` |
| 21 | Batch API pricing | Verified. Haiku 5.5 $0.10 / $0.50 per million tokens (batch $0.05 / $0.25), Sonnet 5.5 $2 / $10 (batch $1 / $5), Opus 5.5 $4 / $20 (batch $2 / $10) | `10` |
| 22 | Papers for the gold set | Found three leads (GameStop committed-minorities paper, crypto pump-and-dump paper, IIMB paper). Data availability still to check | `03`, `09` |
| 23 | Entity resolution | URL-first for repos. Tickers only with a `$` prefix or in finance subs, ambiguous short tickers excluded. Tool names resolved to a repo URL by the extraction step, or dropped | `07` |
| 24 | Gold-set composition | See below | here |
| 25 | What to hold out | The most recent resolved 12-24 months as the test period, plus 40% of the gold set held out before any study of the data (random split with a recorded seed) | `05` |
| 26 | Pool domains? | No. GitHub only at first. Revisit after the baseline works | `07` |
| 27 | Thesis-versus-catalyst check | Phase 1 mostly needs a spike check (did a Hacker News front-page day or release explain the growth, and did the mention come before it). The full LLM check is a phase 2 item. Validate against at least 50 hand-labeled cases before trusting it (placeholder) | `04` |
| 28 | CRSP earlier? | No. Not needed for phase 1. Check whether your school library provides it before paying | `10` |
| 29 | Cold-start evaluation | Report every metric separately by author's prior-post count (0, 1-2, 3-9, 10 or more) and by whether the author is new to the sub | `04`, `05` |
| 30 | Review queue | A weekly report and a CSV you fill in. Later, a small web page | `02` |

### Gold-set composition (default, phase 1, about 150 posts)

- 40 verified hits, stratified by year and subreddit
- 70 matched non-hits, chosen by matching on information known at posting time (subreddit, month, post type, linked repo age) **before looking at outcomes**, so the choice cannot use hindsight
- 20 confounded cases (growth explained by an unrelated spike)
- 20 self-promotional posts that went nowhere (hard negatives)
- 40% of the set held out before studying

Phase 2 would add famous successes, matched failures, and pump-and-dump cases.

## Needs your input

3. **Disk space and RAM.** You have a second, older ThinkPad with more storage that can be dedicated to this. Please send its specs (CPU, RAM, free disk, operating system) when you can. The plan is to measure the size of one subreddit's download first and extrapolate, with a working-space rule of 2-3 times the compressed size.
5. **Where does the live collector run?** Default now: the second ThinkPad, plus the long data pulls. See the hardware section below.
32. **Is the default payoff scenario right?** The money policy assumes a hit doubles the position and a miss can be a total loss. Change it if your intended assets differ. Phase 2 only.
33. **Is the phase order right?** *You answered this: go for the largest upside at the POC stage.* The plan changed in response (see row 1 above and `13`). One thing is unchanged: the evidence I found is skeptical about profit from retail-attention signals, so the first step is a cheap test of the profit link, not the full build.
41. **Second ThinkPad specs:** CPU, RAM, free disk, and operating system.
42. **Is Track B in scope for the POC?** *Answered: yes.* Original note: It is cheap ($0 in model calls) but adds complexity and a manipulation-heavy asset class. Default: yes, as a paper-only kill test (`13`).
43. **Does the orchestrating agent run on API credits or on a Claude subscription?** *Answered: API credits are available but you prefer the subscription. Default in `11`.* This changes how the $60 cap is counted (`11`).
44. **Your labeling time:** *Answered: about 1 hour.* Plan in `11` S7 (hand-label the 60 to 80 most uncertain, LLM labels the rest at lower weight).
45. **Are the human approval gates in `11` (G0 to G4) the right ones?** Add or remove any.
46. **Options in the POC?** Default: no. Free historical options data is limited, and leverage conflicts with the risk-averse stance (`12`).
47. **Dashboard framework:** default is Dash (you know it). Streamlit is faster to start if you would rather.

## Hardware options

Constraint: a roughly $1,000 ThinkPad also used for school and everything else, with $200 build and $25 per month budgets.

What strains the laptop and what does not:

- Fine locally: DuckDB queries, scikit-learn logistic regression, hand-labeling, reports.
- Possible but slow: embedding around a million texts on CPU (hours, unbenchmarked), reading large dumps.
- Not suited: running 24/7 as the live collector.

| Option | Cost | Pros | Cons |
|---|---|---|---|
| 1. Laptop only, plus an external SSD if space is short | $0 to about $90 | No monthly cost, simplest | Not always-on, competes with school work, battery and heat on long jobs |
| 2. Laptop for development plus a small VPS for the collector | about EUR 5.49-5.99 per month (Hetzner CX23 or CAX11 after the June 2026 repricing, one-article source, verify) | Always-on collection, laptop stays free | Monthly fee, some setup |
| 3. Option 2 plus a rented bigger machine by the hour for heavy one-off jobs | a few dollars per job (price not checked) | Handles big embeddings or joins without buying hardware | More accounts and setup |
| 4. A home always-on device (Raspberry Pi or used mini PC) | one-time (price not checked) | No monthly fee | Depends on home network and power, you maintain it |
| 5. Free tiers (scheduled GitHub Actions for polling, free notebook compute for embeddings, BigQuery free tier for GH Archive queries) | $0 | Cheap | Limits and terms change, fragile for a collector (all unverified) |
| 6. Campus research computing or a faculty sponsor | $0 | Real compute | Only if undergrads can get access (unknown) |
| 7. **A second ThinkPad dedicated to this** (older, more storage, specs pending) | $0 | Always-on collector, room for dumps and Parquet files, your main laptop stays free, no monthly fee | Older CPU, so avoid heavy local embedding. Depends on home power and network. You maintain it |

Default lean: **option 7** for the collector and the long pulls (the GitHub star history alone is about 20 hours for 5,000 repos), with the main laptop for analysis and review. The small VPS (option 2) becomes a backup if the home setup proves unreliable, and the external SSD is probably unnecessary. Confirm after you send the specs.

## Things to measure (phase 2 of the plan, not decisions)

13. Real base rate of positives among verifiable mentions, under each definition (top 1%, 5%, 10%).
14. Real haircuts in `05` (train share, decay effective sample size, label confidence, unconfounded share). Currently assumptions.
15. Whether older data helps: recent-only vs all-with-decay on the newest labeled year.
16. Whether the model beats simple baselines, like subreddit growth rate.

## New questions raised

34. **What do engagement fields mean in each period of the dumps?** Plot `retrieved_on - created_utc` by month before using any score or comment count (`03`).
35. **Are the seed subs complete?** Many stop between July and October 2026 in Arctic Shift. Check completeness month by month, and decide how to fill gaps (own collector, other dumps).
36. **User history across subreddits.** User-level features need a user's activity beyond the seed subs. Options: restrict to the pulled set (cheaper, biased toward those communities), or query Arctic Shift by author (rate limits unread). Default: restrict to the pulled set plus expansion subs.
37. **Deleted and removed content.** Default: do not use deleted or removed text as model input, and never publish usernames in any shared output (hash them in any shared file). Confirm after reading Reddit's terms.
38. **Alerts are correlated.** Count independent episodes (cluster by week and theme) when computing precision bounds (`10`).
39. **Independence of the held-out gold slice.** Confirm the 40% held-out split is done before anyone looks at features or patterns.
40. **Which GitHub star-history method?** API pagination (free, slow: about 4 hours for 2,000 repos) vs GH Archive (bulk, heavy). Decide after counting how many repos phase 2 produces.

## Parked

- LightGBM and SHAP comparison, after the logistic baseline works.
- Notifications beyond the weekly report.
- Stock execution or anything touching real money. Not planned.
