# 25 - R0 pilot findings (August 2026, 14 subs)
> **Update (October 14, 2026):** the unit of analysis is the ticker-day and the design effect measured in `28` is 1 to 1.6, not 3 to 4. The weak-case verdicts here are superseded by `28`, `31` and `38`.

Run October 13, 2026 through the Arctic Shift posts API (`scripts/r0_api_pull.py`, polite, 1 s pause, 100 per request). A full-month census, ordered by time, no score filter (`22`). Raw files are not in the repo (kept in the session scratchpad, outside Dropbox). Analysis: `scripts/r0_analyze.py`. **One month, one year. These are not representative of 2005 to 2023, no outcomes are joined yet, and cashtag counts are upper bounds.**

## What was pulled

| Sub | Posts | Per day | Unique authors | GitHub link % | Cashtag % | Removed or deleted % | Link-only posts % | Zero-post days |
|---|---|---|---|---|---|---|---|---|
| wallstreetbets | 5,291 | 171 | 3,636 | 0.0 | 7.5 | 40 | 22 | 0 |
| LocalLLaMA | 3,281 | 106 | 1,945 | 15.5 | 0.5 | 13 | 10 | 0 |
| coolgithubprojects | 1,434 | 46 | 1,109 | 74.0 | 0.3 | 12 | 19 | 0 |
| ValueInvesting | 1,294 | 42 | 790 | 0.3 | 6.8 | 30 | 2 | 0 |
| mcp | 1,293 | 42 | 764 | 25.5 | 0.2 | 23 | 24 | 0 |
| biotech | 1,159 | 37 | 846 | 0.2 | 0.1 | 25 | 22 | 0 |
| investing | 958 | 31 | 737 | 0.0 | 2.5 | 46 | 0 | 0 |
| MachineLearning | 602 | 19 | 443 | 13.0 | 0.8 | 47 | 4 | 0 |
| pennystocks | 554 | 18 | 341 | 0.2 | 30.9 | 22 | 4 | 0 |
| algotrading | 374 | 12 | 249 | 1.6 | 0.3 | 42 | 4 | 0 |
| AMD_Stock | 256 | 8 | 108 | 0.0 | 1.6 | 7 | 49 | 0 |
| smallcapstocks | 148 | 5 | 64 | 0.0 | 19.6 | 11 | 33 | 2 |
| OpenWebUI | 121 | 4 | 92 | 12.4 | 0.0 | 8 | 12 | 2 |
| SecurityAnalysis | 37 | 1.2 | 23 | 2.7 | 0.0 | 11 | 32 | 13 |
| **Total** | **16,802** | | | | | | | |

3,860 GitHub repo links to 1,753 unique repos in the month (across these subs).

## Findings that change the plan

1. **Volume is very uneven, and my rank-1 prior was wrong on volume.** r/SecurityAnalysis (rank 1 in `20`) has about 37 posts a month, with 13 empty days. That is roughly 450 posts a year. r/wallstreetbets alone is a third of the whole pull. The V scores in `20` are replaced by these measured values for the 14 subs.
2. **Resolved-entity volume is small, as Eli suspected.** About 700 posts in the month contain a cashtag (upper bound, includes false hits), mostly from wallstreetbets (about 400), pennystocks (about 170), and ValueInvesting (about 90). That is roughly 8,000 a year in these subs. Against the 100,000 to 1,000,000 resolved posts needed for weak-to-strong signal (`23`), the strong-signal case is within reach over a decade or so and the weak-signal case is not. Name-only mentions (no `$`) are not counted and will add to this.
3. **A large share of posts have no body.** Removed or deleted share is 40 to 47% in investing, MachineLearning, algotrading, and wallstreetbets. For those posts only the title survives, so entity extraction and text features work from titles alone. This is a representativeness issue (`22`): the removed posts are not a random subset (spam, rule breaks).
4. **Cashtag extraction needs a ticker list.** The top "tickers" in MachineLearning and LocalLLaMA are single letters ($K, $L, $D, $P, $N), which are math and parameter notation. wallstreetbets has real ones (HTZ 41, RDDT, MRNA, NVDA). The resolver must match against a listed-securities file and drop one-letter and common-word hits (`04`).
5. **Repo mentions are mostly not "early."** The most-linked repo in the month is ggml-org/llama.cpp with 184 mentions, an established project. Several small repos are linked 10 to 24 times, which looks like the same author repeating a promotion. "First mention in the scanned set" (`14` R3) and author-repeat flags are essential, or the model will learn "frequently linked" instead of "early."
6. **Authors are concentrated in small subs.** The top 5% of authors produce 33% of mcp, 36% of smallcapstocks, and 38% of AMD_Stock posts. User-level features are unstable there, and a few accounts dominate.
7. **Score and comments are not clean.** Retrieval happened about 20 seconds after posting (the first-retrieved time), yet median comments are non-zero in several subs and 24 to 86% of posts have score of 1 or less. The API response also carries a second-retrieval marker, so the fields appear to have been refreshed later. The exact semantics need a check before any use (`04`, `22`). They stay out of features regardless.
8. **Flair is sub-specific.** Coverage ranges from 0% (coolgithubprojects, smallcapstocks) to 100%. A flair feature is a sub interaction, not a general variable.
9. **Timing.** About 60% of posts are during US and European daytime hours. The rest fall outside market hours, so the first tradable price after the post is the next open. That matters for the lead rule (`16`) and windows (`17`).

## Pipeline issues found in the pull itself

- The API returns "Timeout" with an HTTP 422 (not 5xx). The puller now retries on 422, uses limit 100 (not `auto`), and keeps a 1-second pause.
- Several field names are not valid (`domain`, `is_self`, `permalink`, `stickied`, `locked`, `edited`, `num_crossposts`, `removed_by_category`, `upvote_ratio`). The valid set used: id, created_utc, retrieved_on, subreddit, author, title, selftext, url, score, num_comments, link_flair_text, over_18.
- Total about 230 requests for 16,802 posts.

## Updates to earlier docs

- `20`: wave order stays a prior, but volume per sub is now measured for these 14. Do not read SecurityAnalysis as a primary source; treat as a high-quality, low-volume sub.
- `23`: the per-year resolved volume estimate is now about 8,000 cashtag posts in these subs (upper bound), pointing to comments, more subs, name-only matching, and repo-to-company targets as the ways to reach the needed N.
- `19`: add "removed or deleted flag" and "title-only" as explicit variables (post type with no body).

## What R0 did not answer

- Whether outcomes can be joined (no price or GH Archive data fetched yet).
- Any claim about signal. Nothing here tests it.
- Earlier years. The same pull for 2019 and 2021 is the next cheap check, since volumes and removal rates will differ.
