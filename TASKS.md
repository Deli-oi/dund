# Work queue

Status legend: [ ] todo, [x] done. Gate means stop and ask Eli.

## Current queue (October 14, 2026)

- [ ] Census completion and QA (`scripts/census_posts.py`, `census_qa.py`, `field_coverage.py`)
- [ ] Resolver tuning on real posts (`docs/33`)
- [ ] Price pull for resolved live tickers (`docs/34`, log every miss)
- [ ] Label join (`docs/35`)
- [ ] Ticker-day features (`docs/36`)
- [ ] Power sim v2 (net-return lower bound, `38` D8)
- [ ] Pre-registration v2 freeze (`docs/32`) before any outcome join
- [ ] Live input contract and parity test (`38` D12)
- [ ] Paid delisted data decision (USER, `38` D10)

## Eli does (cannot be done by the agent)

- [ ] Buy and set up the VPS (default Hetzner CX23 or CAX11, 40 GB; check price and location). Give Claude Code SSH access only if you are comfortable with it.
- [ ] Create a GitHub personal access token (read-only public data is enough). Put it in `.env`.
- [ ] Decide on Hacker News use (official API, low volume; see `docs/11` source rules).
- [ ] Set a monthly spend limit in the Anthropic API console if any batch LLM jobs will be used.

## Agent queue

### T0. Set up the repo (done)
- [x] `git init`, venv outside Dropbox (`C:\Users\dalele\venvs\dund`), `pip install -e .[dev]`, 9 tests pass. Ledger, confidence, and report modules and `scripts/r0_profile.py` exist.
- Done when: tests pass on the laptop.

### T1. Clean the docs for the new scope (done)
- [x] Scope banners added (done).
- [ ] Update `docs/08` items 34, 35, 36, 37, 40 only after Eli has read them (ask first).
- Done when: no doc describes Reddit training as current, banners removed.

### T1b. Data collection deep dive follow-ups (`docs/14`)
- [x] R0 pilot done (`docs/25`): profile one month of the Arctic Shift data (schema, coverage, field semantics, size). Source in `docs/17`; confirm with Eli where to store it before any download.
- [ ] R1-R3: mention extraction, repo id resolution, first-mention table, entity audit on 100 links.
- [ ] Add the feature registry and run manifests (data snapshot ids, code SHA).
- Done when: profile and audit reviewed by Eli, and the cohort choice (A or B) is decided.

### T1c. Post-first schema and confidence (`docs/16`) (done in part)
- **On hold until the R0 profile has been read with Eli.** Do not build converters before looking at the data.
- [ ] Post table with entity list, voters, `p`, `c`, `label_version`; confidence factors as pure functions with tests.
- [ ] Decide multi-entity rule and type C handling (Eli).
- Done when: schema and tests pass on synthetic data.

### T2. Evaluation harness on synthetic data (harness done, `src/dund/synth.py`)
- [ ] Synthetic generator with a planted signal, label noise, and optional leakage. See `docs/12`.
- [ ] Tests: leakage detection (label-side feature fails the build), label-permutation test (AUC near 0.5), random-feature control, planted-signal recovery, label-noise robustness, walk-forward split with purge and embargo, calibration check (Brier), block bootstrap.
- [ ] Tests of the tests: inject a leak and a shuffled label and confirm the suite catches them.
- Done when: the suite fails on injected bugs and passes on clean data.

### T3. Deploy skeleton
- [ ] Systemd timer templates in `deploy/`, an idempotent setup script (non-root user, firewall, python env, data dir), and a health-check script that logs disk use and last-run times.
- Gate: Eli runs it on the VPS. Do not SSH in without being asked.

### T6. Labels (S4) and leakage tests
- [ ] Cohort percentiles, own small label model, confounder flags. Run the leakage suite from T2 on real data.
- Gate G4.

### T9. Baseline model, calibration, intervals
- [ ] Regularized logistic regression, rolling-origin validation, decay half-life grid, calibration, bootstrap or conformal intervals. Compare with baselines (stars at day 7 and 30, HN presence) per K2.

### T11. Dashboards (`docs/12`)
- [ ] Truth board (sealed test, trial counter, luck meter) and Sandbox (acceptance line, industry filter, all trades in period, sort keys). Dash.

### T12. Optional Reddit daily reader
- Optional live read of new posts, scored by the frozen model. Case file per `docs/11`.

### Status update, October 14, 2026
- [x] T1c unblocked and done in part: `src/dund/schema.py`, `transform.py` (parity test), `entities.py` (resolver, SEC ticker table).
- [x] T2 synthetic harness: `src/dund/synth.py`, `scripts/power_sim.py`, results in `docs/31`.
- [ ] Census: `scripts/census_posts.py` running to `posts_v3` (2012-01 to 2026-09, 14 subs). Check `scripts/field_coverage.py` per year as files land.
- [ ] Tune the resolver on real census posts (blocklists, aliases, share classes).
- [ ] Prices: live tickers via free source (`docs/29`), log every miss. Later: cheap paid history with delisted names.
- [ ] Freeze pre-registration (`docs/32`) before any outcome join.
- Deferred: GitHub-star outcomes (`docs/30`), comment pull (event type only, `docs/28`), VIC.

## Deferred (GitHub outcomes)

Old repo-first tasks, kept for history (`38` section E).

### T4. GH Archive sizing (S1)
- [ ] Define the candidate query (emerging repos, see `docs/11` S1). Run it for **one month only**, record query cost and row counts.
- [ ] Verify the free query allowance and the data source terms; update the docs.
- Gate G1/G2: report counts, cost, and projected positives under the top-1%, 5%, 10% definitions. Stop if fewer than about 300 raw positives are likely.


### T5. Curves and outcomes (S2) and HN attention (S3)
- [ ] Reduce to Parquet. Features up to T, labels after T. Handle right-censoring.
- [ ] HN: official API only, low rate, User-Agent, stop on blocks.
- Gate G3 before large GitHub API pulls.


### T7. Org-to-ticker and token tables (S5)
- [ ] Curate seed table with Eli (market cap band, exposure tag, materiality). Verify against SEC company data.
- [ ] Token-to-repo map from CoinGecko metadata (verify coverage).


### T8. Kill tests (S8, `docs/13`)
- [ ] Event study with placebo dates for token repos (K1), company repos (K1b), and the aggregate index versus ETFs (K3). Report event counts before testing, power, trial counter.
- Gate G5: does the finance link survive? If not, shelve it and keep the tool radar.


### T10. Gold set
- [ ] Select about 150 repos per `docs/11` S6, pre-label with a Sonnet-class batch call, sort by uncertainty, give Eli the top 60 to 80 to judge in about an hour.

