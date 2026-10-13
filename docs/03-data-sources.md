# 03 - Data sources

Items marked (verified) were checked this session. Items marked (unverified) were not.

## Reddit - historical

- **Pushshift** public access was revoked by Reddit in May 2023. Do not plan around it.
- **Academic Torrents:** a comprehensive Reddit dataset maintained by u/Watchful1, with monthly updates, covering 2005-2025. About 4 TB in full, but split by subreddit, so only the subs you need have to be downloaded. Download-only, with no search API.
- **Arctic Shift** (findings below): described by a third-party article as free and covering 2005 to present. It offers bulk dumps plus a public search API (checked this session). There is also a Hugging Face mirror of the archive.
- **Official Reddit API:** no historical search on any tier. Not an option for backfill.

### Arctic Shift findings (verified, October 13, 2026)

- **Bulk dumps:** download links are in the repo's `download_links.md` and on its releases page. The repo ships helper scripts for `.zst` files (Python 3.10+, `zstandard`). New dumps are added periodically, not continuously.
- **API:** public search endpoints for posts, comments, and subreddits. Its rate limits and usage rules were not readable (the repo page that describes them blocked my fetch). Treat it as a volunteer-run service: do not make it the only source of anything.
- **Freshness is near-live for some subs and uneven across subs.** The newest post the API returned was current to within a minute for r/ollama and r/mcp on October 13, 2026, but for other seed subs it stopped between July and October 2026 (see `09-seed-subreddits.md`). The cause is unknown (ingestion gaps or an API quirk).
- **Subreddit metadata is a snapshot from February 2025** (subscribers, post counts), not current.
- **Fresh posts carry ingestion-time stats.** For the newest posts checked, `retrieved_on` was 12-28 seconds after `created_utc`, and `score` was 1. So for recent data, `score` and `num_comments` are what the post looked like seconds after creation, **not final values**.

### Data hygiene to check per month of dump

- The gap `retrieved_on - created_utc` tells you what the score and comment counts mean for that period (near zero means ingestion-time values, large means later values). Plot this by month before using any engagement field as a feature or label.
- Deleted and removed content. Reddit asks API users to remove deleted content and user identifiers (the Data API wiki says to do so, and recommends within 48 hours). Dumps contain deleted items. Decide how to handle them (see `08-open-questions.md`).
- Old subreddits that were repurposed (r/mcp was created in 2010) contain unrelated early content. Filter by date.

## Reddit - live

### What I verified

- Free OAuth access is limited to **100 queries per minute per client ID**, averaged over a 10-minute window.
- **Traffic without OAuth or login credentials is blocked** per Reddit's Data API wiki. This puts the earlier idea of polling subreddit RSS feeds without credentials in doubt. Treat RSS as unreliable until tested.
- Requests need a descriptive User-Agent in the form `platform:app ID:version (by /u/username)`.

### What I could not verify


### Plan

- Primary: a Python poller using PRAW with OAuth credentials, polling each seed subreddit's new posts every 15-60 minutes, and snapshotting each post at fixed ages (for example 1h, 6h, 24h) to capture early-dynamics features. At 100 queries per minute the rate limit is far from binding for a few dozen subs.
- Secondary: Arctic Shift API for gap-filling and reconciliation, since its post feed is nearly real-time for some subs.
- Monthly dumps arrive later and double as a check on the collector.

## Train/serve skew (important)

A dump records a post as it looked when archived. A fresh live post has near-zero score and few comments. Training on one and scoring on the other makes the model see a different kind of input.

1. Do not use fragile post-time features from the dump. Stick to what is knowable at posting: text, author history, subreddit state, linked repos or tickers.
2. For early-dynamics features (score and comments at fixed ages), use only snapshots from the live collector. Dumps cannot recreate these.
3. Check `retrieved_on - created_utc` per period (above) so that any engagement field in training means the same thing as at serving time.

## Outcome data

| Domain | Source | Notes |
|---|---|---|
| GitHub repos | GitHub API with a token, GH Archive | API limit is 5,000 requests per hour (stars with timestamps need many pages per repo, see `10`). GH Archive is the bulk alternative (heavy) |
| Stocks | Stooq, FRED, EDGAR | Free sources can drop delisted companies (survivorship bias) |
| Stocks (paid, later) | CRSP | Survivorship-bias-free. Check whether your school library offers access before paying |
| Crypto | CoinGecko, CryptoCompare, Binance public data dumps | Check liquidity and volume |
| Resale markets | PriceCharting, Wayback Machine | Free history is spotty, sold-price data often missing |

## Event and confounder data

- EDGAR 8-K filings (acquisitions, earnings, leadership changes)
- GDELT (news by date)
- Hacker News API and GitHub Trending for same-week attention (the main confounder for GitHub outcomes: a repo can spike because of one front-page post)
- Related model, paper, or release dates

## Later-reference data (for finding positives, never for features)

- Inbound permalinks to old posts (`/comments/<post_id>/`) from comments or posts made much later
- Phrase patterns ("this post is why I...", "saw this years ago and...")
- Outcome statements ("I bought X after reading this")

## Gold set seed material

- GameStop / r/wallstreetbets is the most studied case. It is a hard example, not a clean positive (see `06-risks-and-pitfalls.md`).
- Leads found (titles verified, contents mostly unread): Lucchini et al., "From Reddit to Wall Street: The role of committed minorities in financial collective action" (arXiv 2107.07361); "The Doge of Wall Street: Analysis and Detection of Pump and Dump Cryptocurrency Manipulations" (arXiv 2105.00733); IIM Bangalore, "The Role of Reddit in the GameStop Short Squeeze." Whether any of them released labeled data is still to be checked.
- The gold set must include matched failures and pump-and-dumps, or it teaches "famous = good." Composition is in `08-open-questions.md`.
