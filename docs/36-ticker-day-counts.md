# 36 - Ticker-day counts (PARTIAL RUN)

**PARTIAL: run on 2026-10-14 while the post census (`posts_v3`) was still being written.** Only files finished at that moment were read (`*.jsonl.gz`; `*.tmp` skipped): 156 files, 12 months, all 2019. Numbers are not final and not comparable across subs until every sub-month is done. Do not cite as the census result.

Method: `src/dund/ticker_days.py`, `scripts/build_ticker_days.py`. Stock candidates only (all match types, any confidence), SEC ticker file `entities/sec_20261014`. Unit is (ticker, UTC date). Repo candidates are in a separate table. Output: `dund-data/derived/ticker_days_20261014_partial/` (`ticker_days.csv.gz`, `repo_mentions.csv.gz`).

## Per year

| Year | Ticker-days | Distinct tickers | Top-10 share of mentions |
|---|---|---|---|
| 2019 (partial) | 29,921 | 2,976 | 25.5% |

Note: bare-ticker and company-name matches are included, so this is wider than the cashtag-only counts in `28`.

## Ticker-days per sub (days with at least one post in that sub; a ticker-day in several subs counts in each)

| Sub | 2019 |
|---|---|
| wallstreetbets | 18,787 |
| investing | 7,534 |
| pennystocks | 3,160 |
| MachineLearning | 1,548 |
| AMD_Stock | 1,324 |
| algotrading | 660 |
| SecurityAnalysis | 627 |
| biotech | 213 |
| ValueInvesting | 88 |
| coolgithubprojects | 70 |
| SmallCapStocks | 39 |

## Resolved-post share per sub-year (at least one stock candidate)

| Sub | Posts | Resolved | Share |
|---|---|---|---|
| AMD_Stock | 3,344 | 1,440 | 43.1% |
| SmallCapStocks | 73 | 33 | 45.2% |
| pennystocks | 6,211 | 1,762 | 28.4% |
| ValueInvesting | 268 | 63 | 23.5% |
| investing | 25,157 | 5,838 | 23.2% |
| wallstreetbets | 70,592 | 16,249 | 23.0% |
| SecurityAnalysis | 2,500 | 456 | 18.2% |
| algotrading | 3,308 | 575 | 17.4% |
| biotech | 1,250 | 176 | 14.1% |
| MachineLearning | 20,822 | 1,551 | 7.4% |
| coolgithubprojects | 1,640 | 67 | 4.1% |

MachineLearning and coolgithubprojects resolve at low rates and are the likeliest source of false stock matches (resolver audit still pending).
