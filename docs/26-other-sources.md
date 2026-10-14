# 26 - Other forums and sources: widening the input beyond Reddit

Written October 13, 2026. Prompted by R0 (`25`): Reddit alone, across 14 subs, supplies about 8,000 cashtag posts a year, which reaches the strong-effect case in about a decade and the weak case not at all (`23`). The decision is to look for more sources with the same kind of input, to pool them in training and to monitor them live.

**Everything below is from my own knowledge and is unverified.** Access terms, coverage years and costs need a primary-source check before any build. Verification is the first task, not the last.

## What "similar input vector" has to mean

Different forums will not have the same distribution. What can be common is the **schema**, one row per item:

`source, item_id, created_at (UTC), author_hash, text, entity_candidates, item_type, parent_id, removed_flag, source_transform_version`

Each source then gets its own extractor into that schema, and `source` stays a model variable (as sub already is, `20`). The shared transform path rule from `22` applies: the same function for training and live input.

Two cautions:

1. **"Known to be factual" is not the same as "early."** A careful, sourced forum is often slower than the market. The ranking below scores both.
2. **Pooling only adds power if the effect is similar across sources.** If it differs, pooled data adds noise. So the detection test (`24`) is run per source family first, then pooled, and the pooled run is a pre-registered second test.

## Candidates

Scores are my priors. C = checkable entity, E = early, Q = information quality, H = history depth, A = access ease (1 to 5, higher is better).

### Finance

| Source | What it is | C | E | Q | H | A | Notes |
|---|---|---|---|---|---|---|---|
| StockTwits | Cashtag-native stream, users self-label bullish/bearish | 5 | 4 | 2 | 4 | 2 | Free labels on every message, so a sentiment target comes cheap. History and bulk access are limited and need checking. High pump contamination |
| Value Investors Club | Member-submitted long and short write-ups with a stated thesis and date | 5 | 3 | 5 | 5 | 2 | Small volume (a few hundred a year), long history, public view delayed for non-members. The closest analogue to r/SecurityAnalysis |
| Seeking Alpha | Contributor articles, plus comment threads | 5 | 3 | 4 | 5 | 1 | Large, tagged by ticker. Paywall and scraping limits make bulk access the main question |
| SEC EDGAR (8-K, Form 4, 13D/G, S-1) | Official filings | 5 | 2 | 5 | 5 | 5 | Not a forum, but it is the highest-quality corroboration source and a label source. Free, full history, RSS for live. Insider purchases (Form 4) are a standard documented signal and give a baseline to beat |
| Bluesky firehose | Open social stream, cashtags in use since 2023 | 4 | 4 | 2 | 1 | 5 | Free live stream, so good for monitoring, short history for training |
| X / FinTwit | Largest cashtag stream | 5 | 5 | 2 | 5 | 1 | Paid API, so only if the budget changes |
| Yahoo Finance boards, Investors Hub, Motley Fool CAPS | Older stock message boards | 5 | 3 | 1 | 4 | 2 | Some defunct or archived. Mostly low quality. Useful as pre-2015 history if archives exist |

### Crypto

| Source | What it is | C | E | Q | H | A | Notes |
|---|---|---|---|---|---|---|---|
| Bitcointalk | Long-running forum with per-coin boards | 4 | 5 | 2 | 5 | 3 | Public, archived in places, many coin launches first appear here. Heavy scam and promo content |
| 4chan /biz/ | Anonymous board | 3 | 5 | 1 | 3 | 3 | Archives exist. Not factual, but early on tokens. Control and attention group, not a positive source |
| Project governance forums (Ethereum Magicians, protocol forums) | Technical proposals and governance | 4 | 3 | 5 | 3 | 4 | Factual, mostly slow, tied to specific tokens |

### Technology and tools (repo and company side)

| Source | What it is | C | E | Q | H | A | Notes |
|---|---|---|---|---|---|---|---|
| Hacker News | Link and discussion stream, Show HN | 4 | 4 | 4 | 5 | 5 | Free API and public dumps, long history, repos are linked directly. Strongest candidate on this side |
| Stack Overflow / Stack Exchange | Q&A, question tag growth as adoption | 3 | 3 | 5 | 5 | 4 | Public data dump (CC licence). Tag growth is a tool-adoption series, not text mentions |
| GitHub issues, discussions, releases (GH Archive) | Events | 5 | 4 | 4 | 5 | 4 | Already planned as outcomes (`11`). Also an input source for repo-side signals |
| Lobsters, Product Hunt, Dev.to | Smaller tech link boards | 3 | 4 | 3 | 3 | 3 | Add only if HN yields |
| arXiv and Hugging Face discussions | Preprints and model community | 3 | 4 | 5 | 4 | 4 | Papers-with-code links repos to papers |

## Proposed first set

Ranked by checkable, accessible and plausibly early, not by how well-known they are:

1. **EDGAR** as a corroboration and label source, and its Form 4 insider-buying signal as a baseline the Reddit model has to beat. Cheap and removes guesswork.
2. **Hacker News**, for the repo and company side.
3. **StockTwits**, if bulk history is obtainable. Otherwise live-only.
4. **Value Investors Club**, small and slow but high quality, for the labelled-thesis gold slice.
5. **Bluesky**, live monitoring only for now.

Crypto sources wait until the equity side shows any signal.

## How this changes the plan

| Item | Change |
|---|---|
| `23` data need | Pooling across source families becomes the main route to scale. Per-source effect heterogeneity has to be tested, and the verdict can be reported per family |
| `24` hypothesis | `U` (source universe) grows to a list of source families, each with its own pre-registered inclusion reason. Adding a source after seeing results counts as a new trial |
| `22` representativeness | Source mix goes into the train-versus-live checks, with the same PSI and adversarial-validation tests |
| Live monitoring | Each source needs a collector with its own rate limit and failure handling. HN, EDGAR and Bluesky have free live feeds. Others need a polling job or are skipped |
| Cost | Extra sources are mostly engineering time and disk, not API fees, unless X is chosen |

## Unknowns to settle before building

1. Bulk or historical access for StockTwits, VIC and Seeking Alpha, and what each permits (terms and rate).
2. Actual volume per source: the same one-month census used in R0 (`25`), one source at a time, before any converter is built.
3. Whether any source has deleted or edited-after-the-fact content the way Reddit has (R0: 40 to 47% removed bodies in some subs), since removal makes training data a biased subset.
4. Entity resolution: cashtag-native sources (StockTwits, Bluesky) are easy. Prose sources (VIC, HN) need the name matcher.

## Next step

A short verification pass, per source: access method, years available, volume per month from a one-month sample, removal behaviour, and cost. Output is a table that replaces the priors above with measured values, same as `25` did for Reddit.
