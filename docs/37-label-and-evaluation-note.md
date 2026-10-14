# 37 - Label and evaluation note

October 14, 2026. Plain-language summary of how labels, features, scoring and live reporting fit together. Sources: `16`, `17`, `18`, `32`. Nothing here adds a new claim or number. Where `32` is still a draft, that is said.

## 1. The ticker is a key, not a feature

The ticker identifies which asset a post is about. It joins a post to its price outcome and groups posts that share a ticker-day for clustering (`32` section 2). The ticker is not part of the signal set `S` (`32` section 4), so the model never sees it as an input at training time.

## 2. Signal features come from posts; price enters only through the label

The signal set `S` is computed from posts: mention counts, distinct authors, subreddit mix, first-mention flag, and text features from a frozen list (`32` section 4). Price does not enter `S`. Trailing price features appear only in the asset-only baseline that the signal must beat (`32` sections 4 and 6). Price enters the training data through the outcome label, which is joined to each post by its ticker (`17`, `16`).

## 3. How held-out posts are scored

- Each held-out flagged ticker-day is a hit or a miss, using the abnormal-return rule in `32` section 5 (benchmark: market plus sector ETF; placebo band; lead rule).
- **Hit rate** is precision: hits divided by flagged ticker-days (`32` section 7).
- **Hurdle:** the claim passes only if the lower 95% bound on precision is above 0.70, not the point estimate (`32` section 8).
- **Calibration:** the model outputs a calibrated probability and interval for each call (`18`, `32` section 5). Calibration is checked on held-out data before any claim.
- **Margin over the hurdle:** `p_lower - p*`, in percentage points, with a z-style version for standard errors (`18`). A positive margin means the lower bound clears the bar.
- Baselines must also be beaten on a paired comparison (`32` section 7).

## 4. Live calls

Live calls are not scored at the time they are made. Each call is recorded with its date, ticker and calibrated interval. When its outcome window closes, it is scored with the same rule as held-out data and added to the track record. Last period's ACT items are reported as hits or misses, with intervals (`18`, rule 4). The truth-board numbers appear on the front page (`18`, rule 5).

## 5. Liquidity floors

Liquidity and size floors are an eligibility filter, not a score input (`17` "Tradable", `32` section 12). A row below the floor is excluded from back data and is not ACT-eligible in live output (`18`, rule 2). The same floors apply to both. The exact floor values are a pending decision (`32` D9).

## 6. What the final live report shows

Each flagged item in the report carries its ticker: the Asset field next to Action (`ACT`, `WATCH`, `SKIP`), post, `p`, interval, threshold, margin and reason codes (`18`, per-item table). The ticker is attached to the action in the report; it is never an input to the score.

## Status

`32` is a draft. Its frozen values (window, floor, sealed dates, minimum flag count) are not yet set. This note describes the intended rules, not results.
