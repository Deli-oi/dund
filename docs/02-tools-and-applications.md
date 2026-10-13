# 02 - Tools and applications

Items marked (verify) are things to check before committing.

## Storage and joins

- **DuckDB + Parquet.** Local, handles hundreds of GB, and SQL makes point-in-time joins (only data from before the post date) much harder to get wrong. Runs fine on a modest laptop at this scale.

## Historical Reddit

- **Arctic Shift** bulk dumps and its search API, plus **Academic Torrents** per-subreddit files, read with Python `zstandard` (dumps are `.zst`).
- Details and verified findings in `03-data-sources.md`.

## Live Reddit collection

- A small **Python poller using PRAW with OAuth credentials**, run on a cron job (or scheduled task) on an always-on machine. Free OAuth access is 100 queries per minute, which is far more than a few dozen subs need.
- Snapshot each post at fixed ages (for example 1h, 6h, 24h).
- **Not RSS-first.** Reddit's Data API wiki says traffic without OAuth is blocked, so unauthenticated RSS may fail (verify before relying on it).
- Arctic Shift's API is a useful second feed for some subs but uneven, so it is secondary.
- Huginn is **not** part of the plan.

## Subreddit discovery

- Build it from the dump, not from live scraping: start from the seeds in `09-seed-subreddits.md`, expand by user overlap and crosspost links, rank by growth.

## Outcome and event data

- **GitHub:** the GitHub API with a token (5,000 requests per hour), plus GH Archive for bulk.
- **Prices (phase 2):** Stooq (bulk CSV), CoinGecko or CryptoCompare for crypto, FRED for macro and rates. `yfinance` is convenient but unofficial.
- **Filings and company events:** SEC EDGAR (8-Ks).
- **News and events by date:** GDELT (free).
- **Paid option for later:** CRSP (survivorship-bias-free stock data). Check whether the school library already provides access.

## Extraction and judgment (LLM)

Current prices (per million tokens, from the Claude API pricing page): Haiku 5.5 is $0.10 in and $0.50 out, Sonnet 5.5 is $2 and $10, Opus 5.5 is $4 and $20, and the batch API takes 50% off.

- A **Haiku-class model with the batch API** for bulk mention extraction, on filtered candidates only.
- A **Sonnet-class model with batch** for the thesis-versus-catalyst check and other hard calls, on a small set. Use Opus only if Sonnet disagrees with hand labels too often.
- Validate any LLM judgment against the hand-labeled gold set before trusting it.
- Hard monthly spend limit set in the API console (check the current option). See `10-risk-policy-and-budget.md` for the cost model.

## Embeddings

- A small open-source sentence embedding model run **locally** (a MiniLM-class model) is free. Speed on the laptop is unbenchmarked, so budget hours for around a million short texts.

## Modeling

- **scikit-learn:** logistic regression with `sample_weight`, calibration (isotonic or Platt), custom rolling-origin splits.
- **statsmodels:** intervals and diagnostics.
- **Label model: write our own** (weighted voting or a simple Dawid-Skene-style model, roughly 50-100 lines). Snorkel's GitHub page says its team is focusing on its commercial product, and I could not see release or commit dates, so I would not build on it.
- **Later, optional:** LightGBM compared against the logistic baseline, with SHAP to read it.

## Interval and abstention

- Bootstrap the training set for intervals, or conformal prediction for coverage guarantees.

## Final selection

- Phase 1: a **weekly review queue** (top k by calibrated probability) delivered as a markdown or HTML report, plus a CSV where you log yes, no, and why. Your judgments become more labeled data.
- Phase 2: a decision rule on the lower confidence bound and the loss/gain ratio, with abstention. See `10`.

## Evaluation, simulation, and dashboards (see `12`)

- **Dash** (Plotly) for the Truth board and the Sandbox, since you already know it. Streamlit is the faster alternative.
- **pytest** for data, leakage, model, simulator, and statistical tests, plus mutation-style "tests of the tests."
- **DuckDB** as the shared store. Dashboards read stored run outputs and never recompute headline numbers.
- Free price data for simulation (Stooq, CoinGecko). Free sources may not include delisted names, so equity results are optimistic until tested otherwise.

## Extra free data for Track A and K1

- **Hacker News search API** for front-page dates of a repo URL (confounder check). Verify the endpoint.
- **CoinGecko** coin metadata for token-to-repo mapping (verify) and daily prices.

## Orchestration

- Start with plain scripts (or a Makefile). Add a workflow tool only if the pipeline gets painful.

## Hosting

- See the hardware options in `08-open-questions.md`. Default lean: develop on the laptop, run the collector on a small VPS (about EUR 5.49-5.99 per month on Hetzner after its June 2026 repricing, one-article source, verify).
