# 40 - Subreddit expansion: candidates ranked by expected ticker-days

Written October 14, 2026. Approved by Eli to widen the census (`38` universe row). All numbers come from the Arctic Shift API: 60 metadata lookups plus 227 post requests (about 290 total, 1 per second). **Rough.** One week per era, capped at 200 posts per window, cashtag-only.

## Method and caveats

- Windows: 2019-08-12..18, 2021-08-09..15, 2026-08-10..16. Up to 200 posts each (2 pages). `+` marks a capped window, so its count is a **lower bound** (the true figure for big subs is higher).
- Ticker = `$XXXX` of 2 to 5 letters, minus ATH YOLO DD CEO USD ETF IPO FOMO EPS GDP FED SEC OTM ITM IV. Name-only mentions are not counted, so value and company subs are under-counted (`28` section 3).
- Ticker-days = distinct (ticker, UTC day) pairs in the sample week. Est. per year = mean over eras the sub existed x 52. Order of magnitude only; one August week is not a year.
- "Empty/removed" = selftext is `[removed]`, `[deleted]` or empty. It includes link and image posts with no body, so it overstates true removal.
- Status: all candidates are public except stockpicks, BiotechStocks, thewallstreet and SecurityAnalysis (restricted, still in the archive). None quarantined or banned. Missing from the archive: Stock_Picks, pennystocks_ (typo), JustBuyIntel.
- Sample cells show `posts / ticker-days` for 2019, 2021, 2026. `-` = sub did not exist yet.

## Ranked table (stock side, num_posts at least 3,000)

| Sub | num_posts | Earliest | 2019 | 2021 | 2026 | Est. ticker-days/yr | Cashtag share | Empty/removed | Recommendation |
|---|---|---|---|---|---|---|---|---|---|
| pennystocks (in census) | 259,636 | 2008 | 131/175 | 200+/71 | 117/40 | 4,957 | 33% | 50% | already in; highest yield |
| SPACs | 36,589 | 2020 | - | 191/68 | 8/1 | 1,794 | 24% | 67% | add (boom-era heavy; 2026 near dead) |
| shortsqueeze | 142,949 | 2020 | - | 200+/25 | 149/35 | 1,560 | 27% | 71% | add (pump-prone) |
| RobinHoodPennyStocks | 95,617 | 2016 | 163/33 | 128/50 | 15/6 | 1,543 | 22% | 66% | add (pump-prone) |
| Biotechplays | 5,234 | 2019 | - | 38/47 | 4/3 | 1,300 | 38% | 52% | add (tiny, very dense) |
| StocksAndTrading | 45,228 | 2013 | 0/0 | 200+/60 | 65/9 | 1,196 | 20% | 69% | add |
| wallstreetbets (in census) | 2,710,687 | 2012 | 200+/24 | 200+/18 | 200+/14 | 971+ | 10% | 77% | already in; cap binds, true value higher |
| StockMarket | 200,702 | 2008 | 175/9 | 200+/32 | 111/10 | 884 | 7% | 64% | add |
| stocks | 449,422 | 2008 | 200+/24 | 200+/11 | 200+/15 | 867+ | 8% | 61% | add |
| wallstreetbetsELITE | 233,740 | 2020 | - | 200+/21 | 113/7 | 728 | 8% | 77% | add (meme-adjacent) |
| Daytrading | 241,515 | 2009 | 88/3 | 200+/31 | 200+/2 | 624+ | 4% | 61% | add |
| Vitards | 13,725 | 2021 | - | 169/21 | 3/0 | 546 | 7% | 67% | add (steel; dead by 2026) |
| weedstocks | 115,675 | 2013 | 200+/14 | 196/11 | 69/3 | 485 | 3% | 87% | add (pump-prone) |
| SwingTrading | 24,826 | 2015 | 7/0 | 53/22 | 179/4 | 451 | 9% | 49% | add |
| options | 157,704 | 2009 | 143/8 | 200+/14 | 121/3 | 433 | 6% | 54% | add |
| dividends | 85,061 | 2009 | 6/0 | 192/21 | 158/2 | 399 | 4% | 31% | add (low removal; name-only mentions likely) |
| thetagang | 53,390 | 2019 | - | 200+/12 | 57/1 | 338 | 4% | 39% | add |
| ValueInvesting (in census) | 64,632 | 2010 | 6/0 | 111/7 | 200+/11 | 312 | 5% | 36% | already in; name-only mentions are the lever |
| EducatedInvesting | 8,687 | 2020 | - | 14/0 | 25/11 | 286 | 8% | 62% | add (small) |
| teslainvestorsclub | 34,245 | 2018 | 41/7 | 105/8 | 13/1 | 277 | 13% | 83% | add (one ticker, TSLA) |
| investing_discussion | 44,599 | 2013 | 15/0 | 165/7 | 97/7 | 243 | 5% | 51% | add |
| investing (in census) | 450,448 | 2008 | 200+/1 | 200+/6 | 200+/5 | 208+ | 2% | 62% | already in |
| PLTR | 22,927 | 2020 | - | 194/8 | 16/0 | 208 | 7% | 74% | marginal add (one ticker) |
| Superstonk | 1,070,373 | 2021 | - | 200+/2 | 200+/5 | 182+ | 3% | 72% | add (GME loop, contamination-prone; cap binds) |
| Optionstrading | 8,844 | 2010 | 5/0 | 0/0 | 200+/9 | 156 | 4% | 34% | marginal add |
| CanadianInvestor | 95,851 | 2014 | 76/0 | 200+/9 | 80/0 | 156 | 3% | 58% | marginal add (TSX tickers, check resolver) |
| RobinHood | 135,228 | 2012 | 200+/3 | 200+/5 | 45/0 | 139 | 2% | 76% | marginal add |
| UraniumSqueeze | 15,043 | 2021 | - | 42/3 | 15/2 | 130 | 7% | 44% | marginal add |
| ASX_Bets | 51,157 | 2020 | - | 200+/5 | 46/0 | 130 | 2% | 70% | marginal add (ASX tickers, resolver) |
| amcstock | 631,630 | 2021 | - | 200+/1 | 22/2 | 78 | 2% | 74% | skip (single-ticker attention loop) |
| DDintoGME | 8,044 | 2021 | - | 100/3 | 1/0 | 78 | 2% | 68% | skip |
| wallstreetbets2, Wallstreetbetsnew | 17,606 / 121,371 | 2015 / 2020 | 0 | 43/3, 0/0 | 29/1, 26/2 | 69 / 52 | 6-8% | 46-47% | skip |
| NVDA_Stock | 18,501 | 2017 | 0/0 | 9/0 | 48/3 | 52 | 5% | 61% | skip (`$` rare) |
| options_trading, GME, RKLB | 6.6k / 391k / 12.9k | | | | | 26 to 35 | 2-7% | | skip |
| SecurityAnalysis (in census), finance, IndianStockMarket, Daytrade, thewallstreet, financialindependence, UKInvesting, StockMarketIndia, IndiaInvestments | | | | | | 0 to 17 | 0-2% | | skip (no cashtags; value subs need name matching) |
| stockpicks, BiotechStocks, TSLA_Stock, tesla_stock, UndervaluedStonks | 17 / 924 / 91 / 179 / 926 | | not sampled (under 3,000 posts) | | | | | | skip |

Cashtag share runs 2 to 38%, highest in small speculative subs. Distinct tickers in the sample week range from 66 (pennystocks) down to 0 to 2 for dead subs.

## Crypto list (kept apart; coin tickers, not stock-side)

| Sub | num_posts | Earliest | 2019 | 2021 | 2026 | Est. ticker-days/yr | Removed | Note |
|---|---|---|---|---|---|---|---|---|
| SatoshiStreetBets | 163,005 | 2020 | - | 200+/19 | 7/2 | 546 | 93% | most bodies empty |
| CryptoMoonShots | 538,946 | 2017 | 10/0 | 200+/20 | 70/7 | 468 | 80% | pump sub, contamination-prone |
| altcoin | 108,652 | 2013 | 171/1 | 200+/15 | 14/1 | 295 | 97% | |
| CryptoMarkets | 353,000 | 2013 | 200+/3 | 200+/9 | 192/4 | 277 | 82% | |
| defi | 67,666 | 2018 | 13/0 | 200+/9 | 84/1 | 173 | 70% | |
| CryptoCurrency | 2,089,701 | 2013 | 200+/2 | 200+/1 | 200+/4 | 121+ | 81% | cap binds |
| ethtrader | 428,910 | 2015 | 200+/3 | 200+/1 | 49/1 | 87 | 82% | |
| Bitcoin, ethfinance | 1.4M / 27.7k | | | | | 0 | | no cashtags |

Crypto yields are low per post because coins are mostly named without `$` (BTC, ETH, "doge"), and 70 to 97% of bodies are empty. Only run crypto if a coin resolver and price source exist (`29`). Not in `expansion_subs.txt`.

## Recommended stock-side add list (25)

SPACs, shortsqueeze, RobinHoodPennyStocks, Biotechplays, StocksAndTrading, StockMarket, stocks, wallstreetbetsELITE, Daytrading, Vitards, weedstocks, SwingTrading, options, dividends, thetagang, EducatedInvesting, teslainvestorsclub, investing_discussion, PLTR, Superstonk, CanadianInvestor, Optionstrading, UraniumSqueeze, ASX_Bets, RobinHood. Written to `C:\Users\dalele\dund-data\expansion_subs.txt`.

## Expected supply

Rough ticker-days per year, from the sample weeks (sum of the 25 adds, cashtags only, capped windows are lower bounds):

| Era | 14 census subs (`28`) | 25 adds only | Combined, before overlap |
|---|---|---|---|
| 2019-like | about 8,000 to 12,000 | about 5,000 | about 13,000 to 17,000 |
| 2021-like | about 24,000 to 34,000 | about 26,000 | about 50,000 to 60,000 |
| 2026-like | about 8,000 | about 7,000 | about 15,000 |

The same ticker-day appears in several subs, so dedup loses perhaps 20 to 35% (a guess, not measured). Net uplift is roughly +60 to 90% in quiet years and +60 to 80% in active years. The adds contribute about 7,000 to 12,000 net ticker-days a year averaged over mixed years, giving roughly 15,000 to 20,000 in quiet years and 40,000 to 55,000 in active ones.

Against `38` (100 bps edge: about 25,000 ticker-days at a 2% flag rate, 100,000 at 0.5%): the 14 subs alone reach 25,000 in about 1 to 3 years. With the adds, about 1 to 1.5 years. 100,000 needs roughly 4 to 7 years of mixed data with the adds (about 2 active years). The 50 bps case (100,000 to 400,000) stays marginal. Name-only mentions remain the largest unmeasured lever and would lift the value and company subs most.

## Risks

- **Pump and promo subs** (pennystocks, RobinHoodPennyStocks, shortsqueeze, weedstocks, wallstreetbetsELITE): contamination-prone (pump coordination, bots, paid promo). Fine for a census; tag by sub so analysis can drop or control them.
- **Attention loops** (Superstonk, amcstock, GME subs): one ticker dominates, so few independent ticker-days per post. Kept for the attention-control role.
- **Single-ticker subs** (teslainvestorsclub, PLTR): few ticker-days and fan bias (`20` caveat 5).
- **Boom-era subs** (SPACs, Vitards, UraniumSqueeze, Superstonk): exist from 2020 or 2021 and are near dead by 2026, so yearly estimates are overstated for 2022 on. The era columns show this.
- **Removed bodies** run 50 to 90% in most subs (inflated by link posts). Titles only, and `27` shows they cannot be recovered.
- **Non-US tickers** (CanadianInvestor, ASX_Bets): need a TSX and ASX symbol list or they give false matches. Drop them if the resolver is US-only.
- **Sample noise**: one week per era, capped. Treat rank order within a factor of 2 as uncertain, and re-rank after the census.
