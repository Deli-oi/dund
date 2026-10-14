# 28 - Raising the sample size: measured levers

Written October 14, 2026. Follows `23` (data need), `25` (R0), `27` (other sources). Numbers are from one month per year (August 2019, 2021, 2026) and one two-hour weekday window per sub for comments. Orders of magnitude only.

## 1. The unit that counts is the ticker-day

Posts mentioning the same ticker on the same day move together, so they are not independent observations. Measured over the 14 subs:

| Month | Cashtag posts | Distinct tickers | Ticker-days | Posts per ticker-day | Top-10 tickers' share of mentions |
|---|---|---|---|---|---|
| 2019-08 | 1,020 | 1,035 | 2,035 | 0.5 | 12% |
| 2021-08 | 4,624 | 1,317 | 2,868 | 1.6 | 23% |
| 2026-08 | 731 | 441 | 705 | 1.0 | 16% |

Distinct tickers can exceed posts because one post names several. Takeaways:

- **The design effect is smaller than the 3 to 4 assumed in `23`**, about 1 to 1.6 in these months, because mentions are spread across many tickers (top 10 hold 12 to 23%).
- **Independent units are about 700 to 2,900 ticker-days a month**, or roughly 8,000 to 34,000 a year from these 14 subs. That is lower than the post counts suggest only in the 2021 meme period.
- **Same-ticker repeats across months are not independent either.** A ticker mentioned every month adds correlated rows. Cluster-robust inference, by ticker, is required.

## 2. Comments

Two-hour weekday window (Tuesday 14:00 to 16:00 UTC, mid-August):

| Sub | Year | Comments | Cashtag | Removed | Median length |
|---|---|---|---|---|---|
| wallstreetbets | 2019 / 2021 / 2026 | 638 / 4,809 / 3,589 | 1.9% / 1.6% / 1.2% | 9% / 21% / 4% | 63 / 35 / 41 |
| pennystocks | 2019 / 2021 / 2026 | 15 / 117 / 40 | 6.7% / 1.7% / 7.5% | 47% / 25% / 5% | 62 / 65 / 45 |
| investing | 2019 / 2021 / 2026 | 329 / 201 / 140 | 0.3% / 0.5% / 1.4% | 9% / 15% / 1% | 114 / 123 / 129 |
| ValueInvesting | 2019 / 2021 / 2026 | 0 / 24 / 103 | 0 / 0 / 1.0% | 0 / 0 / 3% | 0 / 111 / 133 |
| SecurityAnalysis | 2019 / 2021 / 2026 | 9 / 0 / 1 | 0 | 0 | 200 / 0 / 2,412 |

Extrapolated to a month (crude, one window, weekday daytime): wallstreetbets cashtag comments are about 4,400 (2019), 28,000 (2021) and 15,000 (2026), against 766, 3,710 and 394 cashtag posts. Roughly 6 to 40 times the posts.

What comments do and do not give:

- **They add mentions, not independent events.** Aggregated to ticker-day they give an attention and agreement measure (how many distinct authors, how many comments), not new ticker-days. Gain in independent units is modest.
- **Bodies survive much better** (1 to 21% removed against 40 to 69% for posts).
- **They are short** (35 to 65 characters in wallstreetbets), so most hold little beyond the ticker.
- **Value subs have almost no comments in this window.** The comment lever is almost entirely wallstreetbets and pennystocks.

## 3. Levers

| Lever | What it adds | Measured basis | Cost |
|---|---|---|---|
| More calendar years (2012 to 2025 instead of 3 sample months) | Most. Independent ticker-days scale with time | 2,000 to 2,900 per month in 2019 and 2021, 700 in 2026 | API time, about 16 minutes a month for 14 subs at post level |
| More subs (waves 2 and 3, `20`) | Moderate | Small subs contribute little (SecurityAnalysis 37 posts a month) | Same |
| Comments as mentions, aggregated to ticker-day | Low to moderate in independent units, high in attention features | Section 2 | Large pull for wallstreetbets (about 1.3M comments a month in 2026 by extrapolation) |
| Name-only mentions (no `$`) | Possibly large for value subs, where cashtag use is rare (ValueInvesting 87 cashtag posts a month in 2026) | Not measured | Needs listed-ticker and company-name file |
| Continuous outcome and cluster-robust test instead of hit versus miss | Cuts required N several-fold (`23`) | Method, not data | None, pre-register |
| Looser null than the 95th percentile | Cuts required N | Method | Pre-register, raises false-positive risk |
| Other sources (HN, EDGAR) | Adds the repo and company side and baseline signals | `27` | Engineering |

## 4. Projected supply (rough)

Assuming 2012 to 2025 at post level, 14 subs, ticker-days as the unit, and 2019 to 2021 levels as typical (they are the high end):

| Scenario | Ticker-days a year | Over 10 years |
|---|---|---|
| Quiet years (2026-like) | about 8,000 | about 80,000 |
| Active years (2019 to 2021 like) | about 24,000 to 34,000 | about 240,000 to 340,000 |

Against `23`:

- **Strong effect (about 100 to 200k resolved units):** reachable.
- **Weak effect (about 0.5 to 1M):** not reachable from post-level cashtag mentions alone. Comments, name-only mentions and more subs together might double or triple it. That narrows the gap but does not close it.

This is a projection from three sample months. The first real check is the full 2012 to 2025 post-level census, which turns the above from extrapolation into a count.

## 5. Next step

Run the post-level census month by month over the full history for the 14 subs, store raw outside Dropbox, and compute per-month ticker-days. About 14 years at 16 minutes a month is a few days of pull time, and it can run unattended. It needs the disk question settled (`21`), since raw JSONL for the full history is multiple gigabytes.
