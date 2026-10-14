# 04 - Techniques
> **Status: SUPERSEDED in part (October 14, 2026).** The project is now ticker-first, with GitHub-star outcomes deferred, and the study design and decisions in `docs/38-review-decisions.md` and `docs/07-decisions.md` override this document where they differ. Kept for history and for the sections not contradicted.

## Model

Regularized logistic regression, `P(success) = sigmoid(w . x)`, where `x` is only what was knowable at posting time and `w` is learned. Chosen first because every weight is readable. Compare against LightGBM later, but you lose clean weights.

## Unit of analysis

**Updated October 13, 2026: the post is the unit and entities are attached to it (`16`).** The text below is the earlier entity-first wording.

The unit is the thing a post mentions (a repo, ticker, coin, or tool), and the label is that entity's later outcome. Score **every mention**, including the ones that went nowhere, because negatives teach the model what a dud looks like. For credit, first mention only is cleaner and matches the "catch it early" goal.

### Entity resolution (default)

- **Repos:** match by GitHub URL first. This is exact and cheap, and avoids most ambiguity.
- **Tools without a link:** the extraction step proposes a repo URL, and posts with no resolvable repo are dropped, not guessed.
- **Tickers (phase 2):** only with a `$` prefix or inside finance subs, and ambiguous short tickers that collide with ordinary words are excluded. Being conservative here fits the risk-averse stance, since a wrong match produces a false label.

## Features (point-in-time only)

| Group | Examples |
|---|---|
| Content | Compressed text embedding, flags like "I built / benchmarked / open-sourced", links to a repo or paper, count of earlier mentions of the same thing (low prior count = early) |
| Subreddit | Size, 30- and 90-day growth, comments per post, share of builder posts, historical hit rate |
| User | Past hit rate (shrunk), number of posts in the niche, account age, whether the linked repo's owner matches the username, flair |
| Events and context | Related release or paper that week, same-week Hacker News or GitHub Trending, cross-posts, trailing market return and volatility |
| Early dynamics | Score and comments at fixed ages. **Live collector only**, never from dumps |

Karma is mostly noise.

**POC baseline (default):** start with the hand-built features (links, flags, prior mention count, subreddit and user statistics, event context) and add a compressed text embedding only if it improves validation performance. The d versus N budget in `05` is tight, and this also keeps the older second laptop from needing heavy local embedding.

## Point-in-time rule

A user's hit rate must only use outcomes that had already resolved before the post date. Same for subreddit growth and hit rate. Computing over whole history makes the model look great in testing and fail live.

### Engagement fields need a hygiene check

Score and comment counts mean different things depending on when the data was archived. Fresh posts in Arctic Shift carry ingestion-time values (score 1, seconds after creation), not final ones. Before using any engagement field as a feature or label, plot `retrieved_on - created_utc` by month and decide what the field means in each period. Early-dynamics features come only from the live collector's fixed-age snapshots.

## Users and subreddits with little data

- Shrinkage: `(hits + k * prior) / (posts + k)`, computed out-of-fold so a post never sees its own label.
- Prior is the activity-weighted hit rate of the communities the user posts in, not the global average.
- User embedding from a user x subreddit matrix (SVD or a word2vec-style model over the sequence of subs each user posts in).
- `num_prior_posts` as a feature, with user-history features randomly dropped in training so the model leans on community and content signals when history is missing.
- Report cold-start users separately. If accuracy only holds for users with long track records, the model cannot find new people, which is the goal. Report every metric by the author's prior-post count (0, 1-2, 3-9, 10 or more) and by whether the author is new to the subreddit.
- User-level features need a user's activity outside the seed subs. Default: restrict to the pulled set plus discovered neighbor subs (cheaper, but biased toward those communities).
- Out of scope on purpose: inferring individuals' location, employer, or identity, or linking accounts across sites. Aggregate community and topic features are enough.

## Labels

### Outcome-based (primary)

- Repos: growth and persistence compared against a cohort of similar repos from the same period (raw star counts inflate over time).
- Markets: excess return over a benchmark, volatility-scaled (Sharpe-style), with max drawdown as a second number. Add a liquidity filter. Flag pump-and-dump patterns (volume jump at posting time, price collapse within weeks) as negatives.
- Normalize outcomes within cohort: percentile within year, or excess return over that year's benchmark, so a bull-market year does not make everything look like a success.

#### Success definitions (v0 defaults, to be compared)

- **GitHub (phase 1):** star gain over the 12 months after the first mention, as a percentile within the cohort of repos first mentioned in the same month. Success = top 5%. Compare against top 1% and top 10%.
- **Extra votes for the label model:** growth at 3 months, repo still active at 12 months (recent commits), later citations of the post.
- **Spike confound:** flag repos whose growth is dominated by a single day (for example a Hacker News front-page day or a major release). Check whether the Reddit mention came before the spike. If it did not, mark confounded.
- **Markets (phase 2):** excess return over a benchmark at 12 months or more, volatility-scaled, with a liquidity filter. Success = top 5% of the cohort.

### Weak supervision with weights

- Each signal (repo growth, later citations, market-verified outcome, hand labels) is a noisy voter: positive, negative, or abstain.
- Combine votes into a soft label, via a weighted sum through a sigmoid, or a label model (Snorkel-style) that estimates each signal's accuracy from agreement.
- Train the main model on soft labels, either with the probability as the target or by duplicating each example as positive and negative with weights `p` and `1-p`.
- Citation-based votes start with lower weight than market-verified outcomes, since citations carry visibility bias.
- New signals later (Hacker News mentions, funding rounds) are just another voter.
- Needs ground truth: a hand-labeled gold set (100-200) to check and tune weights, kept out of training.
- Correlated signals double count. Check pairwise correlation and down-weight or merge overlapping ones.
- Fit label weights on earlier years and freeze them before touching later ones.
- Report each signal's standalone performance against the gold set.

### Later citations

Find posts that people referenced a year or more later, to discover positives and validate outcome labels. This is **label-side only**. The model must never see it as a feature.

## Sample weights, regularization, and output confidence are three different things

- **Per-example weight:** label confidence x data quality x time decay. Controls how hard each example pulls on the fit. Report effective sample size `(sum w)^2 / sum w^2`.
- **Regularization (L1/L2):** constrains the learned weights themselves. Use it as well.
- **Output confidence:** a calibrated probability plus an interval. A separate thing.

## Time handling

- **Measure outcomes in event time** (days since the post), not calendar year. Compare each post to a benchmark over its own window and include conditions around the post (trailing return, volatility).
- **Calendar time appears only in:** the train/test split (ordering must be real) and decay weights (the platform and its users change).
- **Decay weights:** `w = 0.5^(age / half-life)`. Choose half-life on validation folds, never the final test years. Grid: 1, 2, 3, 4, 6 years, starting guess 3.
- **Horizons:** two checkpoints, growth at about 3 months and persistence at about 12 months. A success grew and held. By domain: GitHub 3-12 months, markets 12+ months. Label at several horizons (3, 12, 24) and see which the features predict best.
- **Right-censoring:** a post too recent to have resolved is unknown, not negative. Exclude it from training.
- **Gap between train and test** equal to the longest horizon, or labels resolve during the test period and leak.
- **Rolling-origin validation:** train 2014-2018, test 2019, then train through 2019, test 2020, and so on.
- **Only new data?** Not by assumption. Test it: train on recent-only vs all-with-decay, compare on the newest labeled year. If old data is stale, the fitted half-life comes out short.
- After validating, retrain on everything (including the test years) before any live use.

## Confounded wins

Example: a post gives a good reason stock X will go up, but X goes up the next day because of an acquisition. It correlates but is a false positive for training.

- Flag big single-day jumps in the outcome window and check what happened (EDGAR 8-Ks, GDELT, news).
- If a catalyst the post never mentioned explains most of the abnormal return, mark the label **confounded** and downweight or abstain. It is neither evidence for nor against the post.
- Check whether the post's own stated thesis matches what happened. Expensive. Hand-label some and test whether an LLM-assisted check agrees.
- Keep confounded cases as a separate test slice to measure how much the model is fooled by luck.

## Risk posture and decision rule

- False positives are very bad. False negatives are acceptable.
- Act only when `p * gain > (1 - p) * loss`, i.e. `p* = loss / (loss + gain)`. Example: 100% loss, 50% gain gives `p*` of about 0.67 before any safety margin.
- Implement by weighting negatives more in the loss or by a high threshold, then recalibrate (cost weighting distorts probabilities).
- The model should abstain a lot.
- A false negative noticed later is a good hard example to add for iterative training, at modest weight, with false positives rechecked on held-out data afterward.

## Calibration and uncertainty

- Calibrate on a held-out validation period (isotonic or Platt). Check a reliability plot: of posts scored 0.7, about 70% should be real successes.
- Track Brier score alongside precision at the top k.
- Intervals from bootstrap or conformal prediction. Cold-start users and new topics get visibly wider intervals.
- Report more than one number per post. Do not multiply probability and expected return into one score until it is shown to predict out of sample.
