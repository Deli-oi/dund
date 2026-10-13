# 12 - Evaluation and simulation suite

Goal: a test suite that shows whether the model has actually learned something from the data, a simulator that shows what trading on its reports would have done, and two separate dashboards, one for the **honest accuracy** and one for **exploring** (where noise is allowed to show).

Nothing here is built yet. The design assumes Python with Dash (you already know it), pytest, DuckDB, scikit-learn, and statsmodels. Dashboards read stored run outputs and never compute headline numbers themselves.

## Core design rule: two boards, one sealed test set

| | Truth board | Sandbox |
|---|---|---|
| Purpose | The real, out-of-sample accuracy. The one number to believe | Play with thresholds, filters, and sorting to see what happens, noise included |
| Data it can see | Sealed test period, evaluated once per pre-registered configuration | Development and validation periods only. The sealed test period is not loaded |
| Who can change settings | Nobody in the app. Configs come from run files with a hash | You, with sliders and filters |
| Labeled as | Final | Exploratory, with a visible banner |
| Every change counts as a trial | No (fixed config) | **Yes.** A trial counter rises, and a "luck meter" shows how much improvement random variants would produce by chance |

**Unsealing the test period is a one-time, logged action.** After it happens, any further tuning contaminates the test set, and the Truth board records that.

## Real machine learning methods in the suite

These are the methods that separate learning from fitting noise:

| Method | What it does here |
|---|---|
| Walk-forward validation with a purge and an embargo | Train on the past, test on the future, with a gap so labels that resolve during testing cannot leak backward |
| Nested validation | An inner loop picks regularization, decay half-life, and threshold. An outer loop measures performance. Tuning never sees the outer test |
| Label-permutation test | Shuffle labels within time blocks 1,000 times, rerun the whole pipeline, and compare the real result to that null distribution. Anything inside the null band is noise |
| Random-feature control | Replace features with random ones and confirm skill is zero |
| Planted-signal test | Generate synthetic data with a known effect and confirm the pipeline recovers it. Generate data with no effect and confirm it finds nothing |
| Label-noise robustness curve | Inject increasing label noise and plot how quickly performance decays |
| Block bootstrap | Confidence intervals that respect clustering by week and theme |
| Calibration (isotonic or Platt) with Brier score and a reliability plot | Checks the probabilities mean what they say |
| Learning curves and regularization paths | Metric against number of training positives, to see where d versus N bites (`05`) |
| Ablations and baselines | Drop each feature group, compare against simple baselines (subreddit growth rank, prior only, random) |
| Fold stability | Metrics and feature weights by year, flagging sign flips |
| Deflated significance | Uses the trial log, so the bar rises with every variant tried (`10`) |

## Truth board contents

1. **Verdict banner:** pass or fail against pre-registered gates: beats baselines, lower bound on precision at or above target, calibration error within tolerance, beats the permutation null at p < 0.01 after deflation, leakage tests green.
2. **Out-of-sample metrics with intervals:** precision at k, recall at a review budget, PR-AUC, Brier score, expected calibration error. Slices: cold-start authors, confounded cases.
3. **Noise audit panel:** observed metrics against the permutation null, the random-feature control, the planted-signal result, and the label-noise curve.
4. **Learning curves and d versus N status:** effective features against effective positives.
5. **Stability:** by year and by fold, with feature-weight stability.
6. **Trial log and deflated significance.**
7. **Calibration plot.**
8. **Test status:** the latest pytest results (below).
9. **Seal status:** sealed or unsealed, and when.

## Test suite

**Data tests**
- Schema and unique IDs, no timestamps in the future, posts per month per subreddit against expectation, duplicates, URL normalization cases, deleted or removed content excluded.

**Leakage tests (the most important group)**
- Every feature timestamp is at or before the post time.
- Perturbing any data dated after the post leaves that post's features unchanged.
- User and subreddit statistics use only outcomes resolved before the post date.
- Label windows start after the post.
- The train/test gap is enforced.
- Projections and scalers are fit inside training folds only.
- The sealed set is never read before unsealing (file access audit).

**Model tests**
- Recovers a planted signal. Finds nothing on shuffled labels. Regularization shrinks weights. Sample weights behave as specified. Reproducible with seeds.

**Simulator tests**
- Trades execute at the next open after the alert, never the same bar.
- Costs are applied. No position opens without price data.
- Delisted assets are handled (see below).
- Accounting identity holds: cash plus positions equals equity at every step.
- Changing prices after the signal date does not change the simulated trade until its execution time.
- A random-pick portfolio lands near the benchmark minus costs.

**Statistical tests**
- Confidence intervals cover the true value at about the stated rate on synthetic data. Permutation p-values are roughly uniform under the null.

**Tests of the tests**
- Deliberately inject leakage (use future information) and confirm the leakage tests fail. Inject a known bug into the simulator and confirm a test catches it. A test that cannot fail does not count.

The Truth board shows each test's name, status, and last run time, so you can see which checks are green, not only that "tests pass."

## Simulator

### Entry and exit rules

- **Signal time:** when the model produced the alert (for historical runs, the post time plus a latency assumption).
- **Entry:** the next market open after the signal (crypto: next day's open).
- **Holding period:** fixed (5, 20, 60, or 120 days) or until a target or stop. Selectable.
- **Position size:** fixed percentage per alert (default 1%), equal weight, or volatility-scaled.
- **Limits:** maximum concurrent positions, maximum exposure per sector, no shorting.

### Realism defaults (placeholders to tune)

| Item | Default |
|---|---|
| Transaction cost, large-cap equity | 5 bps |
| Transaction cost, small-cap equity | 30 to 100 bps |
| Transaction cost, crypto | 10 to 50 bps |
| Liquidity cap | no more than 1% of average daily volume, with an extra 10 bps penalty beyond |
| Delisted without data | assume a total loss, shown as a flagged assumption |
| Survivorship | Free price sources may exclude delisted names. Results on equities are therefore optimistic until tested with delisted securities or CRSP |

### Benchmarks and baselines in every run

- The relevant index or sector fund (SPY, a sector ETF, or BTC)
- Buy every candidate that passed the filter
- **Random-pick portfolios:** 1,000 random selections from the same universe and dates, with the model's result shown as a percentile of that distribution. This is the noise band of the simulator.

### Options

Free historical options data is limited. One guide I read describes free sources as typically delayed chains, end-of-day snapshots, a few symbols, or samples, and full historical chains as usually not free. Options also amplify losses, which conflicts with the risk-averse stance. Plan:

- **v1:** equities and crypto spot only.
- **v1.5 (optional):** a stylized option model (Black-Scholes with realized volatility), labeled clearly as optimistic about fills and spreads.
- **v2 (if wanted):** real option chains from a paid source. Price not found, so unknown.

## Sandbox inputs

- **Acceptance line:** slider on the calibrated probability or on its lower bound.
- **Period:** date range (development and validation only).
- **Trade mode:** take every trade suggested in the period, or only those above the line.
- **Industry filter:** only repos or assets classified into chosen industries (S6 in `11`).
- **Asset class:** equities, crypto, (options later).
- **Sizing, holding period, cost multiplier, liquidity cap.**
- **Sort key** (below).
- **Noise toggle:** overlays the random-pick band and the permutation null on the equity curve.

## Sandbox outputs

Equity curve against benchmarks and the noise band, drawdown, trade table, hit rate, average win and loss, profit factor, turnover, cost drag, per-trade return distribution, results by month, and the percentile versus random-pick portfolios.

## Sort keys and the "which output is most useful" analysis

| Sort key | Meaning |
|---|---|
| Lower bound of calibrated probability | Primary. Conservative and fits the risk-averse stance |
| Expected value after costs | Lower-bound probability times typical gain minus the rest times typical loss, minus costs |
| Calibrated probability (point) | Plain estimate |
| Interval width | Uncertainty. Narrow is better |
| Earliness | Repo age and stars at the time of the mention |
| Novelty | Number of earlier mentions (low is better) |
| Cold-start flag | Whether the author has history |
| Liquidity and capacity | Volume and market cap of the mapped asset |
| Time to resolution | How long until the outcome is known |
| Crowding | Number of alerts in the same week or theme |
| Materiality | How much the repo matters to the mapped asset (`13`) |

For each key the Sandbox shows the **rank correlation with realized outcomes**, precision at k, the spread between the top and bottom deciles, and stability across folds. Choosing a sort key is itself a forking path, so each key tried counts toward the trial total.

## Build order

1. **Harness with synthetic data first.** Generate fake posts, outcomes, and prices with a planted signal. Build the leakage tests, permutation tests, and tests of the tests against it. This needs no real data and can proceed while the long data pulls run.
2. **Truth board** on the synthetic data, then on real data when it arrives.
3. **Simulator** with the placebo baselines.
4. **Sandbox** with the trial counter and luck meter.
5. **Plug in real data** after gate G4 in `11`, and keep the sealed test period out of the Sandbox.

## Open items

- Whether options are in scope for the POC (my recommendation: no).
- Targets for the Truth board gates (precision lower bound, calibration tolerance, permutation p-value). Placeholders are in `10`.
- Which equity price source to use for the simulator, given delisting coverage is unconfirmed.
