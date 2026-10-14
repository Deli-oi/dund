# 27 - Other-source census and the deleted-data question

Written October 14, 2026. Measures what `26` guessed. All numbers are from live probes on October 13 to 14, 2026, one small sample each. Small samples, so read them as orders of magnitude.

## A. Can deleted or removed Reddit bodies be recovered?

| Check | Result |
|---|---|
| Arctic Shift capture lag | 2026-08: median 21 s after creation. 2019-08: about 8 days. 2021-08: about 313 days |
| Removed share in wallstreetbets | 2019: 48%, 2021: 69%, 2026: 40% (`[removed]` or `[deleted]`) |
| 2026 posts removed even though captured within seconds | Yes (about 40%), so the removal happened before capture and the original body was never stored |
| PullPush (second Pushshift mirror), by id, 20 removed posts per period | 2019: 0 of 20 bodies recovered. 2021: 0 of 20. 2026: 1 of 20 recovered, 8 not found, 11 still removed |
| Wayback Machine, one sample post | No snapshot |

**Conclusion:** removed bodies are not recoverable at any useful rate. Plan on titles only for those rows, and treat removal as a feature and as a selection effect (`22`). The titles, timestamps, subreddit and flair of removed posts are kept in the census.

## B. Other sources, access and volume

Reddit through Arctic Shift is the benchmark: no login, one request type, about 16,000 posts in 16 minutes.

| Source | Access today | Measured | History reachable | Versus Reddit |
|---|---|---|---|---|
| Hacker News (Algolia API) | Open, no key | August stories: 21k (2013), 24k (2016), 26k (2019), 23k (2021), 30k (2026). GitHub-linking stories: 700, 1,300, 1,200, 900, 3,100 | 2006 onward | Easier |
| HN comments | Open | 34k to 69k a month through 2021. **2.7 million in 2026-08, unexplained (bots or index artifact)**. Do not plan on it | same | Easier, but check the 2026 spike |
| SEC EDGAR full-text search | Open with identifying user agent | August 8-Ks: about 6,000 (2019 and 2026). Form 4: 10,000 or more a month (capped at 10,000 in the response). 2021 calls failed on network and need a retry | 2001 onward | Easier, structured |
| EDGAR daily index files | Open | Reachable (HTTP 200) | 1990s onward | Easier |
| StockTwits public API | Open, no key, 30 per call | Works, cashtag-native | **Shallow.** A pagination probe on one symbol returned messages back to about December 2025. Older ids returned nothing | Harder for history, fine for live |
| Value Investors Club | Homepage loads | Not measured | Long history, but write-ups sit behind a member login, which I will not attempt | Needs your decision |
| Seeking Alpha | Blocked (bot wall, HTTP 403) | None | Unknown | Much harder, paid route needed |
| Bluesky search (public endpoint) | Blocked (HTTP 403) | None | Since 2023 | Needs an account or a firehose consumer |

## C. What this means

1. **Reddit's full history is the only open source of retail cashtag chatter back to the pre-2021 period.** Everything else cashtag-native is shallow or walled.
2. **The easy, deep, open sources are Hacker News and EDGAR.** They help the repo and company side and supply corroboration, labels and an insider-buying baseline. They do not replace Reddit volume on the stock side.
3. **Recovering deleted Reddit data does not rescue the sample size.** Removed rows stay title-only.
4. **Net effect on `23`:** the weak-effect case is still out of reach on posts alone. The levers left are comments (Reddit and HN), more subs, name-only mentions, and per-source pooled tests.

## D. Open items

1. Retry EDGAR 2021 and measure Form 4 properly (use the daily index, not the capped search).
2. Explain the HN 2026 comment count before using it.
3. VIC: needs your decision on whether to use an account you own, or skip.
4. StockTwits: check depth on a few more symbols before dropping it as history.
5. Verify how Arctic Shift handles the same removal in comments (not measured).
