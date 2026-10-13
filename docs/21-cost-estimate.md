# 21 - Total training cost estimate

Written October 13, 2026. All prices are **from memory and not checked today** (marked verify). Data sizes are assumptions except the 3.8 TB combined archive size, which came from the Arctic Shift magnet link (`17`). This is a range, not a quote. Nothing has been bought.

## Rule: look at the data first

Per Eli, no converters or schema code beyond what exists until the R0 profile has been read. Order: R0 profile (one month, wave-1 subs) → read it together → then decide conversions, features, and the final cost. The code already written (`ledger`, `confidence`, `report`, `r0_profile.py`) is generic and does not depend on the data layout.

## One-time build cost

| Item | What | Assumption | Low | Likely | High |
|---|---|---|---|---|---|
| Reddit ingest compute | One VM for about 1 to 4 days, stream and filter, 4 vCPU class | Python JSON parsing is the bottleneck, several TB uncompressed. Prefilter with `zstd -dc` plus a fast text match to cut it. About 0.02 to 0.05 $/hour (verify) | $1 | $5 | $15 |
| Ingest scratch volume | 200 GB to 1 TB block volume for the days used | About 0.044 $/GB-month, billed hourly (verify). Submissions are likely about 0.8 to 1 TB of the 3.8 TB (unverified) | $3 | $10 | $30 |
| Bandwidth | Torrent into the VM | Usually included in a VM plan's traffic allowance (verify) | $0 | $0 | $5 |
| GH Archive outcome pulls | Star and fork curves for resolved repos via BigQuery | Free allowance 1 TB per month then about 6 $/TB (verify). Column-pruned scans across about 12 years, about 3 to 8 TB total | $0 | $15 | $40 |
| Price data | Stooq, FRED, CoinGecko free tiers | Delisted-stock coverage is weak on free sources. A paid month of a cheap historical API fixes it | $0 | $0 | $30 |
| LLM batch work | Entity tagging, spike checks, gold-set pre-labels | `10` cap is $15 | $3 | $11 | $15 |
| Text embeddings (optional) | 300k posts, about 60M tokens through a cheap embedding model, or CPU on a rented hour | Only if ablation says text helps (`19` A14) | $0 | $1 | $5 |
| Model training | Regularized logistic regression, a few hundred thousand rows by tens of features, walk-forward folds, bootstrap | Minutes on the laptop | $0 | $0 | $0 |
| Reduced data storage | 5 to 30 GB Parquet in object storage | About 0.02 $/GB-month (verify) | $0 | $1 | $2 |
| Subtotal | | | **$7** | **$43** | **$142** |
| Contingency (25%) | Retries, re-pulls after we change inputs | | $2 | $11 | $36 |
| **Total build** | | | **about $9** | **about $54** | **about $178** |

Inside the $200 build budget (`10`) in all three cases. The high case is mostly storing a full terabyte for several days, a paid price source, and big GH Archive scans.

## Recurring cost after the build

| Item | Per month | Notes |
|---|---|---|
| Small collector VM (live feeds, HN, GitHub, prices) | $5 to $8 | The `10` upkeep estimate is $25 per month, so this fits |
| Object storage growth | $0.2 to $1 | |
| Repeat ingest when we change inputs (re-run a month or a year) | $1 to $5 per re-run | Because of the raw filtered layer (`14`), most input changes need no re-pull |
| LLM batch work, ongoing | $0 to $5 | Subscription covers the agent session |
| **Typical** | **$7 to $20** | |

## What drives cost up or down

- **Biggest lever:** how much raw we keep. Month-by-month download, filter, delete keeps the volume near 200 GB and the whole ingest near $10 to $20.
- **Second:** whether the Reddit data lets us pull per-subreddit through the Arctic Shift tool or API (`17`). If it does, the 1 TB torrent route is avoided and ingest drops toward $0 to $5. Limits to verify.
- **Third:** GH Archive scans. Restrict to repo ids that resolved from posts, partition by year, and select only needed columns.
- **Training itself is cheap.** The expensive part of this project is getting and cleaning data, not fitting the model.

## Time cost (not dollars)

| Stage | Wall clock estimate |
|---|---|
| R0 profile of one month | Minutes to an hour once downloaded |
| Full wave-1 ingest | 1 to 4 days of VM time, mostly waiting on torrent speed |
| GH Archive pulls | Hours |
| Hand-labeling gold set | About 1 hour of yours (`11` S6) |

## Open item: laptop disk

I measured about 3 GB free on C: earlier today (472 GB used), and only the C: drive was listed. If you have more space elsewhere (another drive, an external disk), tell me the path and I will re-check. Even with room for a month of data, the full ingest is faster and safer on a VM with a clean volume, and it is cheap.

## Per-subreddit option (explored October 13, 2026)

Three ways to get only our subs instead of the 3.8 TB archive. Sources: the Arctic Shift API page, its download tool page, and a Reddit post about the top-40k release, all read today. Sizes marked (unverified) were not found.

| Route | What it is | Covers | Limits and unknowns |
|---|---|---|---|
| **A. Top-40k per-subreddit torrent** (Watchful1, Academic Torrents) | One submissions file and one comments file per subreddit, zstd NDJSON. Pick individual files in the torrent client | 2005-06 to 2023-12 | The whole set is about 2.5 TB per a library listing (unverified), so the point is to select only our files. Per-sub sizes not found. Subs outside the top 40k are missing (check mcp, OpenWebUI, smallcapstocks) |
| **B. Arctic Shift API** | `GET /api/posts/search` and `/api/comments/search` with `subreddit`, `after`, `before`, `limit` (up to 100, or `auto` up to 1000), `sort`, `fields`. No auth documented | Rolling, including 2024 to now | No fixed rate limit (dynamic, 429 plus reset headers). The docs say to use dumps for massive volumes. Text-field queries can time out. No cursor, so page with `after` and `sort=asc`. Scores and comment counts settle after about 36 hours |
| **C. Arctic Shift download tool (web)** | Enter subreddit or user, choose posts and/or comments, set start and end dates | Any range | Output format and limits are not described. Fine for one-off checks and for R0, not for automation |

### Recommendation

1. **R0 now, tiny:** use route C or B for one month of two or three wave-1 subs (for example r/mcp and r/ValueInvesting). That is megabytes, needs no VM, and fits the 3 GB disk. It answers the schema, field-semantics, and link-share questions.
2. **Backfill 2005 to 2023-12:** route A, selecting only the submissions files for wave-1 subs (and their comments later). Expected total is single-digit to low tens of GB (assumption). Run on the VM if the laptop lacks room.
3. **2024 to now:** route B per sub in date slices, polite request rate, retrying on 429 using the reset header. A few hundred requests per sub at most (assumption).

### Effect on cost

| | Previous estimate | With per-subreddit routes |
|---|---|---|
| Ingest compute | $5 likely | $0 to $3 |
| Scratch volume | $10 likely | $0 to $3 (tens of GB, or none if the laptop has room) |
| Download time | Days | Hours |
| Revised build total, likely | about $54 | **about $30** (GH Archive scans and LLM batch now dominate) |

Caveats: a per-subreddit pull gives posts in the subs we chose, so cross-sub first-seen time (B4) and user-activity features (E4 to E7, which need a user's activity in other subs) will be limited to the pulled set. `14` already notes this bias. We can add a user-history pull from route B later for authors who appear in positive and matched-negative posts, which is a small number of users.
