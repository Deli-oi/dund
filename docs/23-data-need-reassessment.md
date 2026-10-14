# 23 - Data need reassessment (supersedes the numbers in `20` and `21`)
> **Update (October 14, 2026):** the unit of analysis is the ticker-day and the design effect measured in `28` is 1 to 1.6, not 3 to 4. The weak-case verdicts here are superseded by `28`, `31` and `38`.

October 13, 2026. Eli's challenge: we have no basis for saying which subs, variables, or trends hold early signals, and the data need is higher than estimated. **Both are right.** This replaces the "50,000 to 100,000 resolved posts" figure in `20`.

## What we do not know

- Whether Reddit posts carry any early signal about market shifts beyond the asset's own trailing behavior. The literature is thin and mixed (`15`).
- Which subreddits, variables, or user types matter. The wave scores in `20` are my priors about culture, not evidence. They only set the order of the first look.
- The base rate of positives, the resolution rate, and the lift. All of these are measured at R0 and in the first census.

So the project is first a **test for whether any signal exists**, and only then a model-building exercise.

## Power math (rough, one-sided 5%, 80% power, base hit rate 5%)

Alerts needed to show that precision among flagged posts exceeds the null:

| True precision among alerts | Alerts needed |
|---|---|
| 15% | about 43 |
| 10% | about 150 |
| 7% | about 820 |
| 6% | about 3,100 |

Convert alerts to posts: if the model flags about 2% of resolved posts, divide by 0.02. Then multiply by a design effect of about 3 to 4, because posts about the same asset and week are correlated (about 10 posts per asset-event, within-event correlation about 0.3). This is for the **test set alone**. Training needs 2 to 4 times as much.

| Scenario | Resolved posts needed (test plus train) |
|---|---|
| Strong signal (10% vs 5%) | about 100,000 to 200,000 |
| Weak signal (7% vs 5%) | about 0.5 to 1 million |
| Very weak (6% vs 5%) | several million, likely not reachable |

Additional pressure:

- **Many variables.** With 60 candidates and a multiple-testing correction, each coefficient needs roughly 2 to 3 times more rows than a single pre-chosen feature. Sub-group findings (archetype by sub) need 10 to 100 times more.
- **The action bar is far above the null.** Acting at `p* = 0.70` means about 14 times lift over a 5% base rate. If the real signal is weak, the model abstains almost always. That is a legitimate outcome, but it means the report will mostly say "no action."
- **Independent events, not posts, are the real N.** Stocks and tokens are a finite universe. The number of distinct asset-weeks is the binding limit, which is why weak signals may not be reachable from stocks alone.

## What this changes

1. **More data on purpose.** Widen the census: more subs (including the wave 2 and 3 lists), comments as mention sources (`14`), the full 2005 to 2026 range. Comments alone can multiply resolved mentions several times.
2. **A more abundant target.** Add repo and token outcomes as pooled targets with an entity-type interaction. Repo outcomes are free and plentiful, so the lift is estimable even if stocks are thin.
3. **Continuous outcomes.** Model the abnormal return or a rank outcome (and threshold only for the report) so power is not lost to a rare binary label.
4. **Explore before exploit.** First pass uses a **uniform, not yield-ranked, sample** across many subs (cheap: a month or a year each), to learn where posts resolve and where signal lives. Wave order from `20` only schedules the work. It does not exclude anything until data supports it.
5. **Pre-registered detection test.** Before fitting, state the minimum lift we care about, the alert count it needs, and the stopping rule. If the full achievable data cannot power the test, say so and stop, rather than mining for a result.
6. **Kill criteria.** If out-of-time lift over the repo-only or asset-only baseline has an interval that includes zero at the full data available, the finance link is shelved and the tool radar stays (`13`).
7. **Cost.** Wider census raises ingest and storage, but at the per-subreddit scale it is still likely under the $200 build budget. Re-estimate after R0 (`21`).

## What I will not claim

I do not have evidence that a signal exists. These numbers are planning arithmetic under assumptions, and the first real counts replace them.
