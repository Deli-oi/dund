# 33 - Entity resolver tuning on real posts

Scope: `src/dund/entities.py` tuned on the posts_v3 census (finished `.jsonl.gz` files only,
title + selftext + url, `[removed]`/`[deleted]` bodies skipped). Ticker table: SEC
`tickers.csv` snapshot 2026-10-14 (10,447 rows). Helper: `scripts/resolver_eval_run.py`
(seeded sample 42, counts, top tickers, rejected cashtags).

Corpus note: the census is still being written. The baseline run saw 133074 posts; the final run
saw 152569 posts (more finished files). 

## Method
1. Baseline resolver run over all finished files; seeded random sample of 150 resolved
   candidates (post, ticker) and 100 posts containing `$` that resolved to nothing.
2. Each judged by reading the text. A candidate is correct if the post refers to that
   listed company/ticker (platform names such as Robinhood and generic words are errors).
3. Fixes made, then the same 150 sample items re-checked against the new resolver, and a
   fresh seeded sample of 150 drawn and judged.

## Precision (resolved candidates)
| Sample | n | Correct | Precision |
|---|---|---|---|
| Baseline resolver, sample A (150) | 150 | 108 | 72.0% |
| Tuned resolver, same sample A items still resolved | 110 | 104 | 94.5% (42 baseline errors -> 6 remain; 4 of 108 correct lost) |
| Tuned resolver (pre-final blocklist), fresh sample B (150) | 150 | 132 | 88.0% |
| Sample B items after final blocklist round | 139 | 132 | 95.0% (tuned on B; optimistic) |

Honest range for current precision: roughly 88-94%. Templated daily threads ("Your Morning
Coffee", "Pre-Market News", "Significant Insider Trading") produce many low-value but
technically correct mentions.

### Baseline false-positive patterns (sample A, 42 errors)
- Company-name matches on generic one-word names after suffix stripping (Hello Group->MOMO,
  People Inc->PPLI, Emerging Holdings->EMRH, Reddit->RDDT, Bullish->BLSH, Honest->HNST,
  New Germany Fund->GF, International Paper->IP "paper"): about 17.
- Bare uppercase acronyms/words that are tickers (UK, EU, ET, ES, PR, PDT, AP, NC, VIP,
  ACA, ASH, RS, CMC, FUND, COO, RBC): about 17.
- Platform names (Robinhood, Interactive Brokers) matched as stocks: noted, high volume
  (2,267 Robinhood matches in the first tuned pass, removed).
- Other: wrong entity from a shared word (Strategy->MSTR, Barnes & Noble->NE).

### Baseline false-negative patterns (100 `$` posts without a candidate)
About 55 are correct non-matches (dollar amounts). Of ~45 real missed mentions:
- ~33 ticker absent from the table (delisted, renamed or OTC: BBBY, ATVI, TWTR, ITCI, SRNE,
  VMW, GRUB, GPS...). Not fixable in the resolver, a table-coverage issue.
- 5 lower/mixed-case cashtags ($amzn, $crwd, $pg, $Goos).
- 6 bare tickers with price cue but no finance word ("TSLA $420.69", "$116K in CVS play").
- 2-3 names: "Amazon earnings", "Berkshire", typo "Telsa".

## Changes (all in `src/dund/entities.py`)
- Precompiled token-prefix phrase index for company names (full-corpus run 6m43s -> 24s).
- CIK-based dedup: names shared by different CIKs are ambiguous and skipped; per CIK one
  canonical ticker; GOOG/GOOGL, BRK-A/BRK-B collapse to a single candidate (explicit ticker wins).
- Alias table (Google/Alphabet->GOOGL, Facebook->META, Berkshire->BRK-B, ~45 brands) used only
  if the target is in the table; ticker aliases FB->META, SQ->XYZ, GPS->GAP, BRK.B->BRK-B.
- Class shares `BRK.B`, `BRK/B`, `$BRK.B`.
- Lower/mixed-case cashtags accepted at lower confidence, never for common words.
- `NAME_BLOCK` (platforms, indices, places, generic words) and an expanded `SINGLE_NAME_BLOCK`;
  un-aliased one-word names require finance context.
- Expanded `COMMON_WORDS` (countries, trading jargon, ML/GPU/indicator acronyms); 2-letter
  bare tickers need paren/name/price corroboration or two finance words.
- Price cue ("TSLA $420", "$116K in CVS") counts as context for bare tickers.
- SEC title jurisdiction tags (`/DE/`, `/MN`) and trailing "&" stripped from names.
- `resolve_ex()` returns rejected tokens with reasons (used for rejected-cashtag counts).

Tests: 14 new tests in `tests/test_entities.py`; full suite passes (96).

## Counts (final run)
Posts: 152569. Posts with >=1 stock candidate: 30532 (20.0%; baseline run on 133074 posts: 27986, 21.0%).
Stock candidates: 48293. Posts with `$` and no candidate: 9830.

### Per sub-year: posts, posts with candidate, top 40 resolved tickers

- **AMD_Stock 2019**: 3588 posts, 1612 with candidate. AMD:821, INTC:709, NVDA:179, MSFT:129, GOOGL:111, AAPL:78, AMZN:43, QCOM:24, MU:19, TSLA:16, MS:14, BAND:13, VII:12, WFC:11, NMR:11, KLRGF:10, CHUC:9, HPE:9, DELL:7, GS:7, META:7, TSM:7, IBM:6, ASML:6, NFLX:6, MSI:5, AIB:5, BAC:5, TXN:5, AVGO:4, HP:4, UBS:4, GLDI:4, ORCL:3, IT:3, BBY:3, PII:3, WMT:3, PERF:3, NOK:3
- **MachineLearning 2019**: 22688 posts, 1238 with candidate. GOOGL:591, META:122, MSFT:117, AMZN:93, INTC:49, TSLA:47, NVDA:45, AAPL:35, UBER:33, NFLX:13, TWI:9, ADBE:8, SPOT:8, WMT:6, FRQN:5, MCD:4, COUR:4, DTST:4, LYFT:4, SAIC:4, CRM:4, CNC:4, CLUS:3, IBM:3, ORCL:3, FTRKF:3, AWRE:3, QCOM:3, MLP:2, POET:2, AA:2, SAC:2, MOS:2, OP:2, BC:2, CPOP:2, CRF:2, BABA:2, CTO:2, BA:2
- **SecurityAnalysis 2019**: 2662 posts, 407 with candidate. BRK-B:29, TSLA:21, META:20, AAPL:18, GOOGL:18, AMZN:18, UBER:15, PS:14, MSFT:12, DIS:11, JPM:11, LYFT:10, BN:9, PCG:8, NFLX:7, BABA:6, GME:6, GE:5, MS:5, TECK:5, SPOT:5, SBUX:5, BAM:5, HKHC:5, GS:4, DJCO:4, WMT:4, EAF:4, KHC:4, BAC:4, MW:4, KKR:3, ELF:3, CHUC:3, W:3, GLDI:3, COST:3, BYND:3, VALU:3, HHH:3
- **ValueInvesting 2019**: 288 posts, 55 with candidate. BRK-B:8, KHC:3, LSE:2, TECK:2, META:2, DX:2, BLK:2, AAPL:2, MORN:2, UBER:1, PVH:1, GS:1, HMC:1, TSLA:1, DOW:1, BN:1, ROG:1, SRTA:1, CPA:1, CR:1, NIM:1, NWL:1, ADBE:1, NL:1, GE:1, DIS:1, BABA:1, AMZN:1, ARMK:1, TTD:1, FFR:1, OLLI:1, NFLX:1, FIVE:1, BCS:1, EGO:1, PRKA:1, MP:1, F:1, GM:1
- **algotrading 2019**: 3649 posts, 223 with candidate. GOOGL:29, SPY:22, META:16, AAPL:12, COIN:11, AMZN:8, MSFT:8, TSLA:7, IBKR:6, UBER:5, FRQN:5, GS:4, IBM:4, MORN:4, IDE:3, F:3, JPM:3, CME:3, AMD:3, INTC:3, UNG:3, DIS:3, TILE:2, ORCL:2, TRI:2, LTC:2, VXX:2, GOOG:2, SOR:2, MOJO:2, DOW:2, NFLX:2, HLIT:2, ATDRF:2, CPA:1, RH:1, GE:1, BLNH:1, APP:1, SBGI:1
- **biotech 2019**: 1359 posts, 53 with candidate. CODX:6, GOOGL:4, MS:3, SNY:2, AMGN:2, GALDY:2, BME:2, AMZN:2, GSK:1, JPM:1, ZBH:1, TMO:1, CRM:1, PFE:1, PHD:1, MRNA:1, LLY:1, BIIB:1, NVS:1, JNJ:1, CLCS:1, AGMB:1, PRPO:1, CE:1, EVKIF:1, GTBP:1, BMY:1, SPOT:1, EDIT:1, SAY:1, GH:1, CFR:1, KOD:1, AMD:1, AAPL:1, SHMXY:1, ETN:1, MRK:1, CLDX:1, SCYX:1
- **coolgithubprojects 2019**: 1787 posts, 60 with candidate. GOOGL:25, SPOT:10, MSFT:5, META:5, AAPL:4, AMZN:2, MANU:1, DBA:1, NFLX:1, HD:1, IDE:1, INTC:1, AUR:1, DPZ:1, OSS:1, SSL:1
- **investing 2019**: 27758 posts, 5362 with candidate. AAPL:418, AMZN:410, TSLA:355, GOOGL:279, META:232, UBER:226, MSFT:219, DIS:183, SPY:181, BRK-B:161, BA:146, NFLX:132, LYFT:126, BYND:112, GS:94, JPM:94, WMT:79, AMD:75, MS:73, PCG:70, GE:67, MSCI:65, BAC:61, NVDA:60, T:58, WFC:56, KO:54, INTC:54, KHC:53, BABA:52, XYZ:49, MCD:48, PG:48, SBUX:46, F:43, MORN:39, ACB:38, JNJ:37, MO:36, CGC:36
- **pennystocks 2019**: 6211 posts, 1568 with candidate. INKW:109, QPRC:84, SHMP:62, NMEX:62, META:45, UBER:42, KULR:40, GOOGL:36, VYST:34, INVU:31, AMZN:28, ACB:27, LYFT:26, THC:24, PRPO:23, WMT:22, AAPL:20, ACRL:19, JAGX:19, FCEL:19, WKHS:19, TRS:18, GXXM:18, MSFT:17, BPTH:17, SNRG:17, CTRM:16, KRFG:15, RNGC:15, NLST:14, SLS:14, TSLA:13, NEXCF:12, CGC:11, ITHUF:11, CURR:11, CVSI:11, OTLK:11, TAKOF:11, SNPW:11
- **pennystocks 2020**: 721 posts, 141 with candidate. FCEL:18, IBIO:10, HIVE:4, GNPX:4, IBATF:3, AAPL:3, ACB:3, NIO:3, TSLA:3, FTFT:3, SHMP:3, AEMD:3, NNVC:3, GCUMF:2, META:2, AQMS:2, MSFT:2, WAY:2, BLPG:2, OCGN:2, BABYF:2, BBY:2, OTLK:2, RH:2, CNBX:2, PHIO:2, BYND:2, GOOGL:2, FTRKF:2, HYSR:2, PLUG:2, XOM:2, CODX:2, UUU:1, GBR:1, KRFG:1, GROY:1, BPOP:1, GRPN:1, NOK:1
- **smallcapstocks 2019**: 81 posts, 24 with candidate. AMZN:2, MBOT:2, NFLX:1, TENX:1, TNXP:1, EW:1, PSIX:1, FT:1, NBIX:1, AXSM:1, BYND:1, WORX:1, SFIX:1, GMBL:1, CLBK:1, ACB:1, AWX:1, ABUS:1, OXBR:1, CAPR:1, HOPE:1, POLA:1, PRKA:1, XNET:1, IBIO:1, ARCI:1, BNGO:1, FCEL:1, WKHS:1
- **wallstreetbets 2019**: 70592 posts, 16772 with candidate. TSLA:2142, SPY:1297, AAPL:1002, DIS:900, AMZN:749, BYND:709, AMD:688, NFLX:552, UBER:523, META:482, BA:441, MSFT:422, GOOGL:407, SNAP:290, LYFT:287, MU:252, PCG:227, RH:207, NVDA:192, SBUX:182, GS:181, ROKU:179, ACB:175, INTC:173, WMT:168, GME:157, LULU:156, BABA:154, GE:151, JPM:142, CGC:141, NIO:138, BAC:133, MCD:133, COST:125, F:111, XYZ:108, MS:107, TGT:105, QCOM:104
- **wallstreetbets 2020**: 11185 posts, 3017 with candidate. TSLA:814, SPY:234, SPCE:222, AAPL:207, AMD:199, BA:140, AMZN:126, BYND:114, MSFT:112, META:84, INTC:66, NFLX:65, TSM:58, NIO:51, SBUX:45, DIS:45, GOOGL:42, UBER:40, PTON:38, LMT:37, BABA:34, GS:32, ACB:32, MS:29, RH:29, JPM:28, MCD:25, NVDA:24, APT:23, BAC:20, SNAP:19, LKNCY:18, GME:17, XOM:17, MMM:17, GE:16, DOW:15, F:15, ABBV:15, IBM:14

### Rejected cashtags / tokens (top 40, all groups)

Reasons: `cashtag:not_in_table` (symbol not in SEC table: OTC, delisted, renamed or fake), `bare:common_word` (blocklisted word/acronym that is also a ticker), `cashtag:single_letter_*` (math/no finance context), `bare:two_letter_weak_context`.

- `FOR` bare:common_word: 5408
- `HERE` bare:common_word: 5168
- `DD` bare:common_word: 3292
- `AI` bare:common_word: 2869
- `API` bare:common_word: 905
- `AM` bare:common_word: 901
- `UK` bare:common_word: 747
- `PM` bare:common_word: 724
- `ET` bare:common_word: 720
- `USA` bare:common_word: 598
- `EDIT` bare:common_word: 593
- `TD` bare:common_word: 581
- `EU` bare:common_word: 532
- `RL` bare:common_word: 358
- `IT` bare:common_word: 309
- `TV` bare:common_word: 309
- `PRE` bare:common_word: 304
- `PC` bare:common_word: 282
- `PR` bare:common_word: 274
- `NEXT` bare:common_word: 254
- `RSI` bare:common_word: 251
- `ALL` bare:common_word: 238
- `YOU` bare:common_word: 232
- `UP` bare:common_word: 213
- `ON` bare:common_word: 199
- `BTC` bare:common_word: 191
- `IP` bare:common_word: 190
- `NN` bare:common_word: 183
- `RH` bare:two_letter_weak_context: 182
- `NOW` bare:common_word: 175
- `CD` bare:common_word: 160
- `PDT` bare:common_word: 156
- `MA` bare:common_word: 146
- `GO` bare:common_word: 145
- `FCF` bare:common_word: 144
- `RTX` bare:common_word: 143
- `POST` bare:common_word: 142
- `WTF` bare:common_word: 133
- `ICLR` bare:common_word: 133
- `BEAT` bare:common_word: 132

Top not-in-table symbols include $GDET, $BECKY, $AABB, $ARSN, $KALY: mostly OTC pennies and WSB meme tags.

## Remaining known gaps
- Table coverage: the SEC snapshot is current-day, so 2019-2020 tickers that were delisted,
  renamed or acquired (BBBY, ATVI, TWTR, VMW, NRZ, SRNE, ITCI) and most OTC pennies never
  resolve. Fix needs a point-in-time or historical symbol table.
- Templated multi-ticker threads (Morning Coffee, Pre-Market News, Insider Trading lists)
  yield many correct but low-signal candidates; downstream should down-weight by title pattern.
- Mentions of a company as a platform/context (Google in ML posts, Apple as phone) still
  resolve; ML subs show high GOOGL/META counts that are research-org mentions, not stock views.
- Bare tickers without finance words ("get into AMD") and lowercase names/typos are missed.
- Residual bare-ticker acronym collisions (MO, ET, IQ, DAL) and shared-word names (Avista) remain.
- Share-class ambiguity: name matches pick the lowest-ranked ticker (GOOGL, BRK-B); other
  ETFs/warrants of the same CIK are never produced from names.
