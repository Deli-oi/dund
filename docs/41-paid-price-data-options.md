# 41 - Paid price data options (survivorship-free daily US equities)

Researched 2026-10-14 by web fetch of vendor pages. No account created, nothing purchased. "Page" = read from the vendor page that day. "(memory)" = not verified. Context: `29` (free sources fail on delisted names), `38` D10 (cheap paid dataset with delisted names required before confirmatory phase), `35` (label builder wants `date,open,high,low,close,adj_close,volume` per ticker; a series ending early becomes `delisted_or_series_ended`, never False).

## Comparison

| Vendor | Price read from page | Delisted included? / start | Adjusted + corp actions | Format / access | Identifiers for ticker reuse | Limits | Personal / automated licence |
|---|---|---|---|---|---|---|---|
| Norgate Data, US Stocks Platinum | 6-month $346.50, 12-month $630.00. No monthly option. Silver/Gold ($270/$360 per yr) exclude delisted. Diamond 12-month $787.50 | Yes, back to 1990 (Platinum and Diamond) | Page: not detailed. Python package exposes price, corporate actions, index constituent history (secondary source) | Windows-only Norgate Data Updater (NDU) must run; `norgatedata` Python package returns DataFrames; local proprietary DB | Not verified on page. Delisted symbols carry a date suffix (memory, unverified). Historical index constituents included | Local DB; data inaccessible if subscription lapses (secondary source) | Terms not read (EULA excerpt cut off). Free trial linked, details not shown |
| Sharadar Core US Equities Bundle (Nasdaq Data Link) | Price NOT visible without login (QuantRocket page: billed monthly or annually, Non-Professional vs Professional licence) | Per QuantRocket: prices 1998 to present, active and delisted, excludes ETFs | Not read on page (memory: SEP has split-adjusted and dividend-adjusted close, ACTIONS table) | Nasdaq Data Link API / bulk CSV / python | Memory, unverified: TICKERS table with permaticker, CUSIP, dates | Not verified | Non-pro certification needs name and profile URL (QuantRocket page) |
| EODHD, "EOD Historical Data" plan | $19.99/month, or $199.00/year | Search result: delisted symbols listed via `exchange-symbol-list?delisted=1`; after 2018 delisting has EOD+splits+dividends, before 2018 EOD only; "60,191" US delisted symbols (EODHD page). Start year per ticker not verified | Page: EOD plan 30+ years; splits and dividends endpoints (search result); adjusted close (memory) | REST JSON/CSV; 100,000 calls/day, 1,000/min (page) | None verified. User report: asking for a reused symbol returns the NEW company (ABS.US example) | 100k calls/day is ample | Listed under Personal Plans; terms not read |
| Tiingo | Starter $0; Power $30/month or $300/year (individual) | Not mentioned on page (memory: partial) | Not read | REST JSON/CSV | Not verified | Power: 110,256 symbols/month, 10,000 req/hr, 100,000/day, 40 GB/month; Starter 500 symbols/month | "Internal use only", personal use, no sharing (page) |
| Polygon.io (now massive.com) | Basic $0 (2 yrs, 5 calls/min); Starter $29 (5 yrs); Developer $79 (10 yrs); Advanced $199 (20+ yrs), monthly. Annual "saves 20%", figure not shown | Page: "All US Stocks Tickers", delisted not stated. Needs 20+ yrs so Advanced for 2012 and earlier (page: Developer 10 yrs reaches 2016 only) | Not read | REST, flat files (memory) | Not verified (memory: has CIK and composite FIGI in ticker details) | Starter+ unlimited calls | Stocks plans labelled individual / non-professional only (page) |
| FirstRate Data, Stocks Complete | Initial price NOT shown. Updates $59.95/month after one free month ($79 with fundamentals) | Yes: "over 7,000 delisted stocks" plus 9,321 liquid US stocks; Jan 2000 on, ticker starts vary | Adjusted for splits and dividends AND unadjusted both included (page) | Downloadable files, 1m/5m/30m/1h/1d; file format not stated | Not verified. Ticker-keyed files, so reuse risk (unverified) | One-time bulk | Licence not on page |
| Kibot | Daily data one-time packages; All Stocks & ETFs bundle $990; Premium $139/month; custom orders from $40 | Not stated on page | CSV unadjusted, split-adjusted or fully adjusted | CSV, API/FTP on Premium | None verified | 45 days unlimited downloads, 1 yr access | Not read |
| Alpha Vantage | $49.99/month (75 req/min) up to $249.99/month; second list $499 to $2,499 (likely annual, unconfirmed) | Not mentioned on page (memory: LISTING_STATUS has delisted flag; delisted price history uncertain) | Not read | JSON/CSV API | Not verified | per-minute caps | Not read |
| Databento | Standard $199/month, Plus $1,750/month, Unlimited $4,500/month, or pay per GB | Not confirmed; equities daily not confirmed on page; "16+ years" | n/a on page | Binary/CSV API | Multiple symbology systems (page) | n/a | Not read. Built for intraday/tick; poor fit |
| CRSP via WRDS | Not purchasable by an individual from what was found; WRDS fetch returned spam, nothing read | Yes by reputation (back to 1925, memory) | Yes (memory) | WRDS SQL/SAS/Python | PERMNO, CUSIP, historical ticker (memory, ideal for resolver) | Academic only | Needs a university subscription (memory, unverified). Only route: ask a university contact |
| Kaggle / GitHub archives | Free | Search found none with delisted names. Best-known (jacksoncrow) is current NASDAQ listings only, ends 2020 | adj close | CSV | none | none | Mixed. Verdict: not survivorship-free, do not use |

## Recommendation

Requirement: delisted/acquired/bankrupt names, 2012 or earlier, adjusted, personal laptop.

1. **Cheapest that nominally satisfies it: EODHD "EOD Historical Data" at $19.99/month** (page, 2026-10-14). Caveats are real: pre-2018 delistings have prices only (no corporate actions) and a reused symbol resolves to the new company, so the pre-2018 dead names (the ones we most need) are the least certain.
2. **Safest that definitely satisfies it: Norgate US Stocks Platinum, $346.50 for 6 months or $630 for 12 months** (page). Verified: delisted back to 1990, historical index constituents. Not verified: identifier set.

Plan: spend one month on EODHD ($19.99) and run the doc `29` probe set (BBBY, SIVB, TWTR, FRC, SPLK, ATVI, CTXS, WORK, SHLD, HTZ). If pre-bankruptcy BBBY/SHLD/HTZ history and the acquired names come back with correct company names and adjusted closes, stay on EODHD. If not, buy Norgate Platinum 6 months. Ask Sharadar via Nasdaq Data Link for its price (not visible without login); if about the same as EODHD it is the better data (permaticker, CUSIP; memory), since it is designed for survivorship-free work.

## Cost estimate (EODHD EOD plan, page price; excludes tax)

| Term | Cost |
|---|---|
| 1 month | $19.99 |
| 3 months | $59.97 |
| 12 months | $199.00 monthly-equivalent $16.58 (annual) vs $239.88 monthly |

Fallback Norgate Platinum: no 1 or 3 month option; minimum 6 months $346.50; 12 months $630.00. Windows laptop required (user has Windows 11).

Daily bars for 6,000 tickers is about 6,000 calls, well under the 100,000/day limit, so one day's pull covers the full history.

## What we would have to build

1. `scripts/ingest_eodhd.py` (or `ingest_norgate.py`): pull `exchange-symbol-list/US?delisted=1` and the active list, store raw JSON in a vendor snapshot dir with fetch date. Then per ticker pull EOD with `from=2000-01-01`, write gzipped CSV `date,open,high,low,close,adj_close,volume` to the existing `load_prices` layout. Also pull splits and dividends.
2. Mapping table `vendor_symbol -> (company name, exchange, first date, last date, delisted flag, CIK/ISIN if given)`. Join to the SEC ticker table by name and date overlap, since the SEC table is a current snapshot (D10).
3. Reuse guard in the resolver: a mention at date d resolves to a vendor series only if d lies in [first_date, last_date] of that series AND the name matches. If one symbol has two companies, key series by (symbol, company id), not symbol.
4. Sanity checks: series ending on a known acquisition date, no price after last trade, split-adjustment continuity, and compare overlap against the Yahoo files for live names.
5. Record vendor, plan, pull date and licence note in the doc `38` coverage report. Do not redistribute raw files.

## Unverified claims

- Sharadar price, tickers-table fields (permaticker, CUSIP), adjustment method.
- Whether EODHD EOD plan (vs higher plans) returns delisted data via API, per-ticker start dates, whether adjusted close is correct for dead names, and any identifier (ISIN/CUSIP/CIK) in the symbol list.
- Norgate suffix convention for delisted/reused symbols, identifier fields, licence terms, free trial scope, API licence for automated use.
- FirstRate initial one-time price and licence; Kibot delisted coverage; Alpha Vantage delisted price history; Polygon delisted history and Advanced plan depth; Tiingo delisted coverage.
- Databento equities daily coverage.
- CRSP/WRDS individual access (fetch failed). Academic route assumed from memory.
- Kaggle: only a search; no dataset checked directly.
- Any licence permission for scripted bulk download for personal research: no vendor ToS was read in full.
