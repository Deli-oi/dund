# 43. Matched controls and estimator

Status: Current. Implements D1, D3, D4 of `38`. Code: `src/dund/controls.py`.

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
- Ticker-only clustering is run as a negative control. It should be narrower than two-way when weekly shocks exist; it is never used for the verdict.
- Windows 5, 10, 21 form a 3-test family corrected with Holm.
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
