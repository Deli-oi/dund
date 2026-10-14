# Start here

## What this is
dund tests whether posts in 14 finance subreddits (Arctic Shift census, 2012 to 2026) hold early signals about tickers. Research only. Status: census running, code and docs built, no outcome data joined, no signal tested.

## Reading order
`docs/07-decisions.md`, `docs/38-review-decisions.md`, `docs/24`, `docs/32`, `docs/28`, `docs/31`, `docs/25`, `docs/27`, `docs/37`. Then `TASKS.md`.

## Run
- Setup: venv outside Dropbox (`C:\Users\dalele\venvs\dund`), `pip install -e .[dev]`, then `pytest -q`.
- Census: `python scripts/census_posts.py` (writes to `posts_v3`); QA with `scripts/census_qa.py` and `scripts/field_coverage.py`.
- Other scripts: `build_ticker_file.py`, `build_ticker_days.py`, `pull_prices.py`, `power_sim.py`, `resolver_eval_run.py`.

## Data and privacy
Raw data lives outside Dropbox at `C:\Users\dalele\dund-data`, never in git. `DUND_SALT` must be set for any real run; there is no fallback.

## Next steps
See "Current queue" in `TASKS.md`: finish census and QA, tune resolver, pull prices, join labels, build ticker-day features, power sim v2, freeze pre-registration v2.
