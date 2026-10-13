# 06 - Risks and pitfalls

## Data and labeling

| Risk | What goes wrong | Response |
|---|---|---|
| Look-ahead bias | Model sees information from after the post (for example "sub later got big") and looks brilliant in testing | Point-in-time features only. User and subreddit hit rates use only resolved outcomes |
| Survivorship bias (sampling) | Famous successes are easy to find and the thousands of similar duds are not | Score every mention. Include matched failures in the gold set |
| Survivorship bias (data) | Free price sources drop delisted companies, so everything looks like it worked out | Keep in mind for stocks. CRSP is the paid fix, noted for later |
| Right-censoring | A recent post has not had time to resolve and gets treated as a failure | Mark as unknown, exclude from training |
| Confounded wins | Stock rises for a reason the post never mentioned (for example an acquisition) | Flag, check catalysts, mark confounded, keep as a separate test slice |
| Visibility bias in citations | Popular posts get cited more, so citations partly measure virality | Compare cited posts against matched uncited ones with similar early scores. Lower initial weight for citation signals |
| Storytelling bias | People cite successes and a post that led to a win may have led to a loss for someone who never commented | Treat money claims skeptically. Verify with market data on the asset |
| Verifying the asset, not the person | Price data shows a stock rose, not that the commenter bought it or that the post caused it | Use as an outcome label for what the post pointed at. Never as proof of a story |
| Pump and dump | Coordinated promotion followed by a price collapse | Flag volume jump at posting plus collapse within weeks as negatives |
| Liquidity | A small cap that "10x'd" on tiny volume may have been impossible to trade at those prices | Liquidity filter on market outcomes |
| Entity collisions | Short tickers collide with ordinary words | URL-first for repos, `$` prefix or finance subs for tickers, exclude ambiguous short tickers |
| Spike confound (GitHub) | Repo growth caused by one Hacker News day or a release, not by the Reddit mention | Flag single-day-dominated growth and check whether the mention came before the spike |
| Uneven data coverage | Some seed subs have posts missing for months in Arctic Shift | Check completeness month by month. Fill gaps with the live collector or other dumps |
| Reused subreddits | Old subs repurposed for a new topic (r/mcp was created in 2010) carry unrelated early content | Filter by date |

## Modeling and evaluation

| Risk | What goes wrong | Response |
|---|---|---|
| Train/serve skew | Dumps can hold final or ingestion-time scores depending on the period, while live posts have near-zero scores | Post-time features only from dumps. Fixed-age snapshots from the live collector. Check what engagement fields mean per month |
| Correlated alerts | Alerts in the same week or theme succeed or fail together, so precision looks more certain than it is | Cluster by week and theme, count independent episodes |
| Multiple testing | Trying many variants produces a lucky best one (about 2.3 standard errors of luck at 50 variants) | Log every variant tried, demand a higher bar (t of about 3), see `10` |
| Slow live proof | Proving a Sharpe ratio live takes years (about 4 to 8 years at Sharpe 1.5) | Judge live results by precision and calibration, keep money out until the gates in `10` |
| Empty profit link | Early GitHub growth may not move any tradable price, and the one careful retail-recommendation study I found showed no abnormal returns | Run kill test K1 first, keep the tool radar as the fallback (`13`) |
| Underpowered kill test | Crypto is so noisy that hundreds to thousands of independent events are needed to detect a small effect | Read a null result as "no large effect," not "no effect." See the power table in `13` |
| Overfitting through the Sandbox | Trying thresholds, filters, and sort keys until a curve looks good is itself fitting noise | Trial counter, luck meter, sealed test period, one-time unseal (`12`) |
| Optimistic simulation | Free price data can omit delisted names, and fills at the signal bar are unrealistic | Next-open entry, costs, liquidity caps, assume total loss on delisting without data (`12`) |
| Agent cost overrun | The orchestrating agent's own tokens can dominate the budget | Per-stage caps, spend ledger, kill switch, checkpoints, scripted stages (`11`) |
| Truncation bias in outcome pulls | Skipping very large repos (the biggest winners) would remove the best positives | Pull everything within a request budget, fall back to GH Archive for very large repos (`11`) |
| Evaluation circularity | Building features by studying cited posts, then testing on those same posts | Hold out before looking |
| Leakage through labels | Citation counts feed 2019 labels but leak into 2019 features | Features from before the post date, labels from after |
| Leakage through the split | Labels in late training resolve during the test period | Gap equal to the longest horizon |
| Tuning on test years | Adjusting label weights until test precision looks good | Fit on earlier years, freeze, then test |
| Correlated signals | Repo growth and citations both partly measure popularity, so they double count | Check correlation, down-weight or merge |
| Soft labels hiding a bad signal | A weak signal quietly averaged in | Report each signal alone against the gold set |
| Tiny positive set | A handful of huge winners makes a signal look real | Check results without the top few winners |
| One outlier | GME can dominate a small positive set | Report with and without it |
| Hindsight in hard-example mining | The misses you notice are the ones that became famous | Add at modest weight, recheck false positives on held-out data |
| Distorted probabilities | Class weights and soft labels distort logistic regression's probabilities | Recalibrate on held-out data |
| Too many features | 457 raw features vs a budget of 10-30 effective ones | Structured features, compressed embeddings, regularization |
| Confidence is not expected return | Multiplying them into one score can hide that a high chance of a tiny win and a modest chance of a huge win differ | Report multiple numbers |

## GameStop as a gold-set case

The early value-thesis posts and the January 2021 spike are widely attributed to different mechanisms (short interest and options dynamics). That makes it a real example of the right outcome for a different reason. Treat it as a hard case, and report results with and without it.

## Privacy and ethics

- Scores on individual usernames are possible. They are public data, but keep that analysis local and do not publish a "best users" list.
- Do not infer individuals' identity, employer, or location, or link accounts across sites.
- Any reading of a user's stated role in a post is a transient model input, not a stored per-person dossier.

## Platform and legal

- Reddit's API terms and rate limits have changed several times. Check before building the live collector.
- Do not put anything built on this data into a product without sorting out the terms.

## Money

This is a research design, not investment advice. The plan is to keep real money out of it until the model has run live and made predictions that could be checked over a few months.
