# 43. Matched controls and estimator

Status: Current. Implements D1 to D4 of `38`. Code: `src/dund/controls.py`.

## Consistency with labels and the seal (revision)

- Timing: a ticker-day with UTC date d has decision time 00:00 UTC of d+1; entry is `labels.entry_index` (first close strictly after). Matching features use only price rows with index below the entry index and posts dated before d.
- Outcome: for flagged and control days alike, `labels.label_event` CAR over the window minus the 20 bps round-trip cost (`net_outcomes`). Nothing is re-implemented.
- Seal: a day is never a control if `sealed.is_sealed_event` is true for its decision time and window, or for its feature look-back (45 calendar days). Flagged sealed days are reported as unmatched with reason `sealed`. Passing `sealed.UNSEAL_TOKEN` as `unseal_token` lifts this.
- Exclusion: a control must be more than max(10, window-1) entry days from every ticker-day with posts (flagged or not).
- The momentum gate of D4 is not implemented here.

## What it does

For every flagged ticker-day we look for an ordinary day of the same ticker that looked alike just before the decision time but was not flagged. The outcome difference (flagged window minus control window, abnormal return) is the quantity of interest. Its mean across pairs is the net abnormal return.

## Selection rules

- Candidates: same ticker, within 40 trading days (about 8 weeks) either side, and more than 10 trading days from any flagged or posted day of that ticker.
- Each control window (10 days by default; 5 and 21 as robustness) must not overlap another chosen control window.
- Matching variables: trailing 5-day and 21-day return, last-day volume over its 30-day average, trailing 21-day volatility, prior 5-day mention count. All are computed from days strictly before the decision day; the tests check that changing later data changes nothing.
- Nearest neighbour on standardized features (SD pooled over candidates and flagged days), caliper 1 SD on every feature, no replacement, greedy in time order.
- Flagged days with no acceptable control are dropped and counted by reason (`caliper`, `no_candidates`, `no_history_or_outcome`). A large dropped share must be reported, because it changes who the result applies to.

## Estimator

- Point estimate: mean of flagged-minus-control differences.
- Uncertainty: two-way multiplier bootstrap (independent exponential weights on tickers and on calendar weeks), one-sided 95% lower bound. The claim holds only if the lower bound is above zero.
- The bootstrap SE is multiplied by sqrt(G/(G-1)) and the bound uses a t(G-1) critical value, G = the smaller of ticker and week cluster counts. Without this the plain percentile bound was anti-conservative when few distinct weeks carry the flags (false-positive rate 0.089 in the calibration world below).
- Ticker-only clustering is run as a negative control, never used for the verdict.
- Windows 5, 10, 21 form a 3-test family corrected with Holm. `run_estimand(events_csv, prices_dir, windows=(5,10,21))` reads the `scripts/build_exploratory.py` output (all rows are posted ticker-days; with no `flag_col` all rows are treated as flagged, i.e. event versus quiet day, not a model verdict), and prints aggregates only.
- Balance report: standardized mean differences before matching (flagged vs all eligible days) and after (matched pairs). Large residual differences mean the match failed.

## Assumptions

- Same-ticker days close in time share the same ticker-level conditions apart from the matched features.
- Flagging is unrelated to future abnormal return given the matched features (conditional independence).
- Abnormal return is correctly benchmarked (D3).

## What it cannot rule out

- Unobserved information (news, earnings, insider activity) that triggers both the post and the move.
- Posts that cause the attention itself: control days are quieter days, so some difference can be generic attention rather than the signal.
- Spillover: controls near flagged windows in calendar time share market-wide shocks only partly; the 10-day exclusion reduces but does not remove contamination.
- Selection from dropped flagged days, thin tickers with few controls, and bootstrap behaviour with few clusters.
- Multiple testing beyond the 3-window family (other variants must be counted separately).

## Calibration (tests/test_controls.py)

Null world: 30 tickers, 250 days, no flagged edge, a market-wide weekly shock (sd 3%) in every abnormal return, idiosyncratic sd 3%, flagged days of all tickers clustered in 8 shared weeks. 1,000 replications, 199 bootstrap draws, run in about 20 s with multiprocessing. The simulation builds candidate tables directly (speed); label consistency is tested separately on real `PriceSeries`.

| Test | False-positive rate (nominal 0.05) | 95% Monte Carlo interval |
|---|---|---|
| Two-way (with small-cluster correction) | 0.061 | 0.046 to 0.076 |
| Two-way, raw percentile bound (before correction) | 0.089 | 0.071 to 0.107 |
| Ticker-only | 0.340 | 0.311 to 0.369 |

The test asserts two-way within [0.01, 0.08] and ticker-only above 0.08. Caveat: the world has only 8 flag weeks, so the result depends on that count; with fewer distinct flag weeks the bound is still expected to be loose.

## Momentum eligibility gate (D4, docs/38 F4)

A flagged (or event) day, and every control, is eligible only if its trailing 5-trading-day abnormal return versus the benchmark (ending at the last close at or before decision time, rows strictly before the entry close) lies within +/- 2 SD, where SD is that of non-overlapping 5-day abnormal returns of the same ticker over the preceding 252 trading days. Status is `pass`, `out` or `unknown`; `unknown` (insufficient history or missing benchmark) is ineligible and reported separately. Note: 252 days hold only about 50 non-overlapping blocks, so "at least 60 observations" is implemented as at least 60 trading days of history and 11 prior blocks. `momentum_gate=True` is the default of `match_controls`, `match_all` and `run_estimand`; results carry `gate` counts (flagged_out, flagged_unknown, control_out, control_unknown), and gated flagged days appear in `unmatched` as `gate_out` / `gate_unknown`. Tests: run-up gated out, quiet drift passes, no look-ahead, short history unknown.
