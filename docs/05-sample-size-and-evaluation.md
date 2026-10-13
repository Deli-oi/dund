# 05 - Sample size and evaluation

All numbers here come from a planning script with assumed inputs. They are estimates, not measurements. The real positive rate is unknown until the counting step (phase 2) is run.

## Key point

For logistic regression, the binding constraint is the **number of positives**, not the total number of posts. The usual rule is roughly 10-20 positives per free parameter (the same idea as N about 10 x d_VC from class, where N is the minority class count).

## Assumed haircuts on raw positives

| Step | Assumption |
|---|---|
| Share landing in train | 60% |
| Effective sample size after time decay | 60% |
| Label confidence | 70% |
| Unconfounded | 70% |

Together that keeps about 18% of the raw count. These are guesses and should be replaced by measured values.

## Training side: maximum features

| Raw positives | Effective | Max features at 10 per | Max at 20 per |
|---|---|---|---|
| 100 | 18 | 2 | 1 |
| 300 | 53 | 5 | 3 |
| 1,000 | 176 | 18 | 9 |
| 3,000 | 529 | 53 | 26 |
| 10,000 | 1,764 | 176 | 88 |

A first sketch of the feature set had **457 raw features** (384 of them the text embedding). That is about 2.5 times over budget even at 10,000 raw positives. Ridge shrinks the effective number of parameters, so this is not a hard wall, but it shows where the pressure is.

### Consequences

- Target about **10-30 effective features**.
- Use structured features: one shrunk user score and one subreddit score each count as one feature, not hundreds of one-hot columns.
- Compress the text embedding to 5-10 dimensions with a projection fit **inside each cross-validation fold** so it cannot leak.
- Consider pooling domains (GitHub, crypto, stocks) to raise positives, with a domain indicator.

## Test side

| Goal | Needed |
|---|---|
| Precision 80%, 95% CI of +/-10% | about 61 alerts |
| Precision 80%, +/-5% | about 246 alerts |
| Precision 90%, +/-10% | about 35 alerts |
| Precision 90%, +/-5% | about 138 alerts |
| Claim precision at least 80% with zero false positives | 13 consecutive true positives |
| Claim at least 90% | 28 |
| Claim at least 95% | 58 |

Planning numbers use a Wald approximation. Wilson intervals are more accurate, especially at high precision.

### How many test positives

| Alerts wanted | Precision | Recall | Test positives | Total positives (test = 20%) |
|---|---|---|---|---|
| 60 | 0.8 | 0.2 | 240 | 1,200 |
| 60 | 0.8 | 0.1 | 480 | 2,400 |
| 60 | 0.9 | 0.1 | 540 | 2,700 |
| 150 | 0.8 | 0.2 | 600 | 3,000 |
| 150 | 0.8 | 0.1 | 1,200 | 6,000 |
| 150 | 0.9 | 0.1 | 1,350 | 6,750 |

Recall values are assumptions.

### False positive rate

- Verifying a tiny FPR is expensive. For about 2.5 false positives in 20M test negatives, FPR is 1.25e-7, and confirming it takes about 24M negatives.
- After the pre-filter to verifiable mentions, about 200k negatives is enough, which is workable.
- That FPR only holds on the filtered pool. The filter's misses count against recall, and its error rate on the full stream still has to be measured.

## About "one in a million"

That figure was a rough guess, not ground truth. At a literal one in a million, 100M posts gives about 100 positives, which supports 1 or 2 features. The real rate among verifiable mentions is probably much higher. Measure it (phase 2) under three definitions of "positive": top 1%, 5%, and 10% of cohort outcomes. If positives come in under about 1,000 for the chosen domains, go simpler: fewer features, heavier regularization, or broader sources.

Widening the target (top 1-5% instead of "unicorn") makes the model find *good* posts rather than unicorns. Unicorn-level labels can stay as a tiered evaluation slice.

## Test set rules

- **Never rebalance the test set.** Downsampling negatives in training is fine (correct probabilities afterward). The test years keep the true base rate.
- **Hold out a gold slice before studying the data**, so features are not built on the same posts used to test.
- Use a time-based split with a gap, plus rolling-origin validation.
- Spend real data on test. Test positives needed (240+) are comparable to training positives.

## Metrics

- Precision at top k (for example top 20 picks)
- Recall at a fixed review budget ("if I read 20 posts a week, how many real hits do I catch")
- PR-AUC
- Brier score and a reliability plot
- Number of false positives among alerts
- Intervals on every metric
- Results with and without GME, and with the top few winners removed

Accuracy and ROC-AUC mislead at this base rate.

## What to claim

With a few hundred positives, claim something like "precision of at least 70% at the top 20 picks, with a wide interval." Nothing finer.

## Independence and clustering

Alerts are not independent. Posts in the same week, theme, or market regime tend to succeed or fail together, so the effective sample size is smaller than the alert count. When computing precision bounds (see the tables in `10`), cluster by week and theme and count independent episodes, not alerts. Expect wider intervals than the simple tables above suggest.

## Held-out plan

- Test period: the most recent 12-24 months with resolved labels, with a gap equal to the longest horizon.
- Gold set: 40% held out by a recorded random split before anyone studies features or patterns.
- Cold-start slice: metrics reported separately by the author's prior-post count.
- Confounded slice: reported separately.

## Compare against simple baselines

Always compare against dumb baselines, like ranking by subreddit growth rate. If the model does not beat them, a fancier model will not fix it.
