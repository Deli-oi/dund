# 30 - Repo-side outcomes: GH Archive / GitHub API feasibility

Probed 2026-10-14 with HEAD and range requests only (about 9 MB downloaded in total). Items marked UNVERIFIED were not tested.

## 1. GH Archive raw hourly files (HEAD, Content-Length)

| Hour sampled | Size (gz) | x720 h = approx. month |
|---|---|---|
| 2012-03-01 12h | 0.97 MB | 0.7 GB |
| 2013-06-01 12h | 2.35 MB | 1.7 GB |
| 2015-01-01 12h | 2.67 MB | 1.9 GB |
| 2015-06-01 12h | 10.8 MB | 7.8 GB |
| 2019-06-01 12h | 26.3 MB | 18.9 GB |
| 2021-06-01 12h | 84.9 MB | 61 GB |
| 2025-06-01 12h | 60.3 MB | 43 GB |

Caveat: each figure is a single hour (a Saturday midday). Diurnal and weekly variance is likely about +/-50%.

Rough totals: 2019-2025 (84 months) is about 3-3.5 TB gz. 2012-2026 is about 4 TB. Every file must be downloaded in full, because there is no server-side filter. Downloading and parsing 3 TB is feasible only on a cloud box or a long job, not on a laptop.

## 2. WatchEvent (stars) presence

Parsed the first 1-4 MB of each sampled hour (partial, truncated gz). WatchEvent is present in all four eras:

- 2012-03: 270 of 2,975 events (9%). Full file, 0.97 MB.
- 2015-06: 879 of 10,340 events (8.5%).
- 2019-06: 232 of 3,726 events (6%).
- 2025-06: 196 of 4,918 events (4%).

- The type was called WatchEvent even in 2012, when "watch" meant what is now "star" (GitHub renamed it in 2012). Treat it as a star event for the whole period.
- The archive begins 2011-02-12. Pre-2015 events use the older "legacy" schema (repo and payload shape differ, e.g. `repository.owner/name` vs `repo.name`). The parser must handle both.
- ForkEvent is present in all eras, so forks come from the same pass. New contributors can be derived from PullRequestEvent and PushEvent, but they are partial (PushEvent author info changed after 2015).
- Caveat: events from 2012 onwards have data gaps and outages in some hours (UNVERIFIED which).

## 3. GitHub REST API, unauthenticated

- `GET /rate_limit` returned core limit 60/hour per IP. Search and code_search are also 60 (the search figure was not separately read).
- `GET /repos/{o}/{r}` works unauthenticated. It returns `stargazers_count`, `forks_count`, `created_at`, etc. It costs 1 request. 1,000 repos is about 17 hours at 60/hour. Only the current snapshot is returned, with no history.
- `GET /repos/{o}/{r}/stargazers` with `Accept: application/vnd.github.star+json` returned **401 "Requires authentication"** unauthenticated. This is the endpoint that carries `starred_at`, so it needs a token. Do not create one without the user's consent.
- With a token (UNVERIFIED): 5,000 requests/hour and 100 stargazers per page. Cost is about stars/100 requests per repo. 2,000 repos of median 500 stars is about 20k requests (4 hours). A repo with 100k stars costs 1,000 requests. Whether pagination is capped for very large repos is UNVERIFIED.
- The star endpoint gives only currently-existing stars (unstarred users vanish). It gives no forks or contributor history, which need separate endpoints (`/forks`, `/contributors`, `/commits`).

## 4. BigQuery `githubarchive` (UNVERIFIED, not signed in)

- Tables: `githubarchive.day.YYYYMMDD`, `githubarchive.month.YYYYMM`, `githubarchive.year.YYYY`. It needs a Google Cloud project. A project with billing is needed beyond the free tier (1 TB query/month, UNVERIFIED current terms).
- On-demand pricing is about $6.25/TB scanned (UNVERIFIED current figure). Cost depends on columns referenced, not WHERE filters.
- A monthly `SELECT repo.name, COUNT(*) ... WHERE type='WatchEvent' GROUP BY 1` must read the `type` and `repo` columns. The estimate is on the order of 10-40 GB per month of recent data, so about 0.3-1 TB for the whole 2019-2025 window, which is about $2-6 (UNVERIFIED). Using a `JOIN`/`IN` against a small uploaded repo list does not reduce the scan.
- Safer approach: run `--dry_run` first to read exact bytes billed.

## 5. Cheapest path: stars/week for ~2,000 repos, 2019-2025

Ranked:

1. **BigQuery one pass (recommended, if user approves a Google account).** Upload the 2,000 repo names as a table. Run a `year`/`month` table query counting WatchEvent grouped by repo and week (also ForkEvent in the same scan). Expected cost is single-digit dollars or free tier. It gives full-history timestamps including unstarred events, and takes minutes. Dry-run first.
2. **GH Archive local stream** (no account, free, slow). About 3 TB download. Run on a cloud VM near GCS, filter by a repo set in `jq`/Python (`zcat | grep -F`), and keep only WatchEvent/ForkEvent rows. Expect about 1-3 days at 100-300 Mbps. Cost is egress or time only.
3. **REST stargazers with a token.** Fine for small repos only. It misses removed stars and is slow for large repos. Use it for spot-validating options 1 and 2.
4. Public ClickHouse GitHub-events playground (UNVERIFIED availability): free, no billing, queryable via HTTP. Worth testing before BigQuery.

Recommendation: use option 4 if it works, otherwise option 1. Use option 2 as the no-account fallback. The unauthenticated REST API is not viable for star history.
