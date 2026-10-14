# 29 - Free historical price sources (probed 2026-10-14)

Sample: AAPL AMD GME AMC BBBY SIVB TWTR FRC LUMN CVNA plus SHLD, HTZ, SPLK, ATVI, CTXS, WORK
(the last 5 are 2015-2024 acquisitions/delistings; HTZ/SHLD are post-bankruptcy re-listings under the same ticker).
Probe: one request per ticker, daily, 2012-01-01 onward. Downloads in scratchpad `prices`; nothing signed up for.

## Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart)

| Item | Result |
|---|---|
| Access | Plain HTTP GET, no key, no login (User-Agent header needed). Unofficial API. |
| Coverage, live tickers | AAPL/AMD/GME/LUMN 2012-01-03..2026-05-28 (3621 rows); AMC from 2013-12-18; CVNA from 2017-04-28. Adjusted close present (plus div/split events). |
| Delisted coverage | FAILED. BBBY 400; SIVB, TWTR, FRC, SPLK, ATVI, CTXS, WORK all 404. Only HTZ and SHLD returned, and only post-reorg history (HTZ from 2021-07, SHLD from 2023-09), so pre-bankruptcy rows are lost. |
| Limits | Undocumented; throttles/429 under bulk use (not hit at ~16 requests; heavy limits unverified). |
| ToS | Yahoo terms restrict automated/commercial use; API is unofficial. Treat as research-only, risk of blocking. |
| Verdict | Good for currently listed names; unusable for survivorship-free labeling. Note the survivorship signature: dead tickers are simply absent. |

## Stooq (stooq.com/q/d/l/?s=xxx.us&i=d)

| Item | Result |
|---|---|
| Access | Plain GET returned an HTML JavaScript browser-verification page, not CSV, for every ticker (8 tried). Scripted download is currently blocked. |
| Coverage / delisted | Unverified (no data obtained). Historically Stooq carried some delisted US names, but cannot confirm. |
| Limits / ToS | Unverified; site has a daily-hit limit historically (unverified). ToS not reviewed. |
| Verdict | Not usable via simple HTTP now. Would need a real browser session; unverified. |

## FRED (fred.stlouisfed.org/graph/fredgraph.csv?id=...)

| Item | Result |
|---|---|
| Access | No key for CSV graph endpoint. DGS10 returned 200 (269 KB) on retry; SP500 timed out once on first try. |
| Coverage | Index/rates only (SP500 series is limited to roughly the last 10 years by licensing, unverified). No single stocks. |
| Verdict | Useful for market benchmark (excess returns) and risk-free rate only. |

## SEC EDGAR (data.sec.gov XBRL APIs)

| Item | Result |
|---|---|
| Access | No key; requires descriptive User-Agent. Twitter (CIK 1326380) dei shares-outstanding returned 200, so delisted filers ARE covered. |
| Coverage | Shares outstanding / financial facts only, not prices. Filing-date granularity. |
| Limits | 10 requests/sec fair-access policy (from SEC docs, not tested). Bulk use permitted within that. |
| Verdict | Good for market cap / share counts including dead companies. |

## Not probed (limits from vendor documentation; unverified, no sign-up done)

| Source | Free tier (unverified) | Delisted? |
|---|---|---|
| Alpha Vantage | Key required; ~25 requests/day; full history `TIME_SERIES_DAILY_ADJUSTED` is premium. Has a LISTING_STATUS endpoint with delisted=state (unverified). | Partial, unverified |
| Tiingo | Key required; ~50 symbols/hour, ~1000 requests/day, 500 unique symbols/month; ToS forbids redistribution. Some delisted names included (unverified). | Partial, unverified |
| Polygon.io | Key required; 5 calls/min; ~2 years history on free tier; includes delisted via active=false (unverified). | Yes but history too short |
| EODHD | Key required; 20 calls/day, 1 year history on free tier. | Too limited |

## Recommendation

1. No free source verified here provides survivorship-free daily prices. Yahoo silently drops the highest-signal names (BBBY, SIVB, TWTR, FRC), so using it alone biases results toward survivors, and mention-return labels for bankruptcies would be missing, not zero.
2. Use Yahoo (adjusted close) as the base for live tickers, and explicitly log every mentioned ticker that returns 404 as "no price data" so missingness is measurable and reportable rather than dropped.
3. Add FRED (SP500/DGS10) for benchmark and EDGAR for share counts; EDGAR also confirms a company existed, which helps classify 404s as delisted vs typo/non-ticker.
4. For delisted coverage, next candidates to test: a browser-driven Stooq download (unverified), a one-month paid Tiingo/Norgate/CRSP-style dataset (not free), or a hand-built list of terminal outcomes (bankruptcy = -100%, acquisition price) for the top few hundred delisted tickers by mention count, sourced from EDGAR 8-Ks.
