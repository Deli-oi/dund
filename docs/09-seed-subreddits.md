# 09 - Seed subreddits
> **Status: SUPERSEDED in part (October 14, 2026).** The project is now ticker-first, with GitHub-star outcomes deferred, and the study design and decisions in `docs/38-review-decisions.md` and `docs/07-decisions.md` override this document where they differ. Kept for history and for the sections not contradicted.

## Domain choice

Updated: this is now **Track A of two** (see `01-plan.md` and `13`). Track B tests crypto tokens that have repos, starting with no Reddit data at all, so no extra seed subreddits are needed yet. The filtering criteria an agent would use to select and expand subreddits are in `11-data-collection-runbook.md` (stage S1).

**Track A domain: AI and developer tooling, with GitHub repos as the outcome.** Reasons:

- Outcomes are objective, free to look up, and resolve in 3-12 months.
- No money is at risk, so a wrong alert costs reading time, not capital.
- It avoids the survivorship and delisting problems of free stock data.
- It fits an AI/ML focus, and spotting tools early is a product-management skill.

**Phase 2 domain: markets (stocks, crypto).** Later, after the GitHub pipeline works. It reuses the same machinery but needs a stricter risk policy (see `10-risk-policy-and-budget.md`).

## How these were checked

Each subreddit was looked up in the Arctic Shift subreddit API. The subscriber counts, creation dates, and post counts below come from its metadata snapshot, which is **dated February 2025**, so they are not current. The "newest post" column is the newest post the Arctic Shift post API returned on October 13, 2026.

Freshness is uneven. Some subs are current to the minute, others stop weeks or months back. That could be gaps in ingestion or an API quirk, and the pull step must check completeness month by month. See `03-data-sources.md`.

## Tier A: core seeds (small to mid-size, builders showing projects)

| Subreddit | Subscribers (Feb 2025) | Created | Posts (Feb 2025) | Newest post in Arctic Shift |
|---|---|---|---|---|
| r/ollama | 46,415 | 2023-07-08 | 13,573 | 2026-10-13 |
| r/LLMDevs | 54,435 | 2023-02-17 | 24,170 | 2026-08-10 |
| r/LocalLLM | 40,015 | 2023-03-26 | 31,742 | 2026-09-01 |
| r/mcp | 2,007 | 2010-10-17 | 16,690 | 2026-10-13 |
| r/Rag | 13,778 | 2021-08-17 | 8,366 | 2026-10-11 |
| r/AI_Agents | 73,732 | 2023-04-28 | 39,943 | 2026-09-01 |
| r/LangChain | 46,550 | 2023-01-26 | 16,022 | 2026-08-11 |
| r/OpenWebUI | 4,341 | 2024-02-24 | 3,491 | 2026-07-10 |
| r/coolgithubprojects | 56,736 | 2014-04-21 | 31,811 | 2026-07-30 |

Notes:

- **r/mcp** is a tiny community in the snapshot (about 2,000 subscribers) around a protocol that later saw wide adoption, which makes it a good test case for whether early posts about specific servers or repos preceded GitHub growth. It was created in 2010, so its early posts are likely unrelated content. Filter by date when pulling.
- **r/coolgithubprojects** is directly about showcasing repos, so it gives clean links to labeled outcomes.

## Tier B: large subs (contrast and spillover)

| Subreddit | Subscribers (Feb 2025) | Created | Posts (Feb 2025) | Newest post in Arctic Shift |
|---|---|---|---|---|
| r/LocalLLaMA | 328,652 | 2023-03-10 | 130,286 | 2026-07-24 |
| r/opensource | 254,110 | 2008-01-25 | 110,282 | 2026-07-26 |
| r/selfhosted | 473,081 | 2014-07-08 | 132,275 | 2026-07-29 |

These are not small, but they carry a lot of repo-sharing posts and give a baseline for how much a subreddit's own size and reputation matter.

Tier A plus B total about 559,000 posts as of the Feb 2025 snapshot, before comments. The cost model in `10` assumes roughly 1.6 times that now. That growth factor is a guess.

## Tier C: finding the actually small communities

The goal is small communities, and a hand-picked list will miss most of them. Phase 1 should expand the seeds automatically:

1. From the pulled data, build a user overlap graph (which subreddits share users) and a crosspost graph.
2. Rank neighbors by recent growth and by share of "I built / released" style posts.
3. Verify each candidate in the same API, and add the promising ones.

Unverified starting guesses to check in that step: r/ClaudeAI, r/ChatGPTCoding, r/commandline, r/neovim, r/rust, r/devops, r/SideProject, r/homelab.

## Phase 2 seeds (markets, not started)

Verified to exist in the Feb 2025 snapshot:

| Subreddit | Subscribers (Feb 2025) | Role |
|---|---|---|
| r/algotrading | 1,773,708 | Builder-flavored finance posts |
| r/wallstreetbets | 17,721,592 | GameStop gold-set case |
| r/Superstonk | 1,142,822 | GameStop-focused community |
| r/pennystocks | 2,034,298 | Likely source of promotional posts (negative examples). To be confirmed from data |
| r/CryptoMoonShots | 2,138,261 | Likely source of promotional posts (negative examples). To be confirmed from data |

r/SecurityAnalysis could not be checked (the lookup failed), and it is unverified. These are large communities, so small-community discovery for markets will again rely on the graph expansion.

## Gold-set literature leads (verified to exist, details still to read)

- Lucchini et al., "From Reddit to Wall Street: The role of committed minorities in financial collective action" (arXiv 2107.07361). Finds that rising commitment among Reddit users preceded the January 2021 GameStop price surge.
- "The Doge of Wall Street: Analysis and Detection of Pump and Dump Cryptocurrency Manipulations" (arXiv 2105.00733). Whether its data is public is still to be checked.
- IIM Bangalore, "The Role of Reddit in the GameStop Short Squeeze" (lead only, details unread).
