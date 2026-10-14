# 16 - Post-first data model, impact scores, and confidence

Decision of October 13, 2026 (Eli). Supersedes the repo-first framing in `14` section 2 and the "unit is the entity" line in `04`. Everything else in `14` and `15` still applies.

## Decision

> **Alignment to `38` (October 14, 2026), read first.** Where this doc and `38` disagree, `38` wins.
> - **Unit (D2):** the modelling and test unit is the **ticker-day** (ticker, UTC date). Post-level `p` and `c` below are inputs that feed the ticker-day aggregate (one function, D12); they are not the unit of the claim or of clustering (cluster key: ticker).
> - **Primary label (D1, D3):** the continuous 10-trading-day net abnormal return (after assumed round-trip cost). The hard hit (yes/no) is descriptive. The horizons 3, 12, 24 months below belong to the repo/tool radar, not the market model.
> - **Windows (D3):** one primary window (10 days); 5 and 21 are pre-registered robustness, not selected on.
> - **Voters:** the voter table is exploratory weighting only. Weights fit on the voters are never used in the confirmatory verdict. The 64 to 252 day voter in `17` is not implemented.
> - **Down-weighting by decisiveness** (`w = c x ...`): `d` is computed from the label, so weighting by it is label-conditional selection. Allowed for exploratory training only. It is not part of the confirmatory estimand, which uses all eligible flagged and matched-control ticker-days unweighted by `c`.

### Glossary: the three confidence notions (defined once here)

| Name | Where | Defined as | Used for | Relation |
|---|---|---|---|---|
| `c` (label confidence) | `16` | `d x q`: decisiveness times evidence quality, on a training label | Exploratory training weight, review queue, hard-label sets | Describes the training example. Never shown as a live prediction confidence |
| margin | `18` | Lower bound of live `p` minus break-even precision `p_be` (D1) | ACT/WATCH/SKIP decision | Consumes the calibrated interval from `37`; it is a decision quantity, not a probability |
| calibrated interval | `37` (with `18`) | Calibrated probability plus interval for a new post or ticker-day, checked on held-out data | Live output and track record | Independent of `c`. The margin is computed from its lower bound |

Chain: `c` shapes what the model learns (exploratory only); the model emits a calibrated interval; margin turns the interval into an action.

- **Input point: the post.** Every post from the exported Reddit dataset in scanned subreddits is a row. Nothing is dropped because it lacks a repo.
- **Repos (and tickers, tokens) are checked along the way.** When a post mentions a checkable entity, we resolve it and look up what happened afterward. The entity supplies outcome evidence for the post, and it is not the row.
- **Each post gets an impact label `p` and a confidence `c`.** `p` is our estimate that the post was an early signal that mattered (yes versus no). `c` says how much to trust that estimate. Training weight uses both.
- Weights for the label voters are fit and re-fit from the data as we see it (`14` section 5 process).

## Row types

| Type | Definition | Label | Used for |
|---|---|---|---|
| A. Resolved entity post | Post mentions at least one entity we resolved to an id with outcome data | Soft label `p` from entity outcomes | Training and evaluation |
| B. Unresolved mention | Looks like it names something checkable but resolution failed or is ambiguous | `p` unknown, low `c` | Entity-resolution audit, feature learning only if explicitly weighted |
| C. No checkable entity | Question, discussion, news, meme without a trackable subject | No outcome-based label. A separate "post impact" signal may exist (below) | Negatives for "does this post lead to anything checkable," never as confirmed "no signal" |

Type C must not be treated as a negative for signal quality, or the model learns "has a link" and calls it a skill.

## What "actual impact" means

Three layers, kept as separate stored fields so the definition can change later without a re-pull:

1. **Entity outcome (primary).** Entity's later performance versus its cohort or benchmark: repo star-gain percentile, ticker excess return, token return. Computed at several horizons (3, 12, 24 months) and stored raw plus percentile.
2. **Lead (timing).** Days between the post and the start of the move, and whether this was the first mention within the scanned set. A post that arrives after the move started has no early-signal value even if the entity won.
3. **Post effect (secondary, caution).** Did the post itself draw attention: score, comments, cross-posts, later mentions of the same entity, entity star or volume change in the days right after. This measures reach, not truth. It is stored and tested, but cannot be the sole basis for a positive label, since it can be caused by the post itself (`14` section 3).

`p` is built from layers 1 and 2, with layer 3 as a low-weight voter at most.

## Label voters (weights learned, `04` weak supervision)

| Voter | Votes yes when | Votes no when | Abstains when |
|---|---|---|---|
| Cohort outcome at 12 months | Top x% of cohort | Bottom or middle | Censored or cohort too small |
| Growth at 3 months | Above threshold | Below | Censored |
| Persistence at 12 months | Still active or still above benchmark | Dead or reverted | No data |
| Lead rule | Mention preceded the move start | Mention came after the move started | Move start undefined |
| Confounder check | n/a | Single-day spike or catalyst not named in the post | No spike detected |
| Later citations (label side only) | Post or entity referenced a year or more later | n/a | No citations |
| Post effect | Strong follow-on attention | n/a | Default |
| Hand label (gold) | You say yes | You say no | Not labeled |

Weights are fit on earlier years, frozen, then checked on later ones, with each voter's standalone accuracy reported against the gold set.

## Confidence score `c`

Two ingredients, kept apart:

- **Decisiveness** `d = |2p - 1|`. A soft label near 0 or 1 is a clear no or yes. Near 0.5 it is a coin flip.
- **Evidence quality** `q`, a product of factors in [0, 1] (placeholder values, tune on the gold set):

| Factor | Lower when |
|---|---|
| Entity resolution | Fuzzy name match, ambiguous ticker, renamed repo |
| Outcome measurement | Thin data, illiquid asset, few stars, bot-star flag, missing prices |
| Horizon completeness | Right-censored at some horizons |
| Voter agreement | Voters disagree (use label-model variance or entropy across votes) |
| Confounder risk | Spike days, known catalyst, attention-only dynamics |
| Timing clarity | Move start ambiguous, first mention uncertain because of dump gaps |

**`c = d × q`**, reported to the viewer with the reason codes that pulled it down.

How the three numbers are used:

| Use | Rule |
|---|---|
| Training weight | `w = c × time_decay × data_quality`. Report effective N `(Σw)² / Σw²` (`04`) |
| Hard-label sets (gold, sealed test) | Only rows with `c` above a stated cutoff, so the test set is the clean cases. Report results at several cutoffs |
| Review queue | Rows with moderate `p` and low `c` go to you first, since a human label there is worth the most (`11` S6) |
| Abstain rule | Live model output keeps its own calibrated probability and interval (`04`). `c` here describes the training label, not a live prediction |

Do not confuse the two confidences: label confidence `c` (how sure we are about this training example) and output confidence (calibrated probability and interval for a new post).

## Stored per post (schema sketch)

`post_id, created_utc, subreddit, author_hash, post_type, text_ref, entities[] (id, kind, resolve_method, resolve_conf, first_mention_flag), outcomes_by_horizon{}, lead_days, voters{}, p, d, q_factors{}, c, label_version, data_snapshot_id`

`label_version` changes whenever voter weights or definitions change, so old and new labels coexist and can be compared on the same rows.

## Consequences for earlier docs

- `14` section 2 (R1 to R5): keep extraction and resolution, but the output feeds a **post table with an entity list**, and R3 first-mention becomes a field, not a filter.
- `14` section 4: cohort A versus B still applies per entity outcome. Add "cohort size too small" as a `q` factor and a voter abstention.
- `04` Unit of analysis: replace "the unit is the thing a post mentions" with the post-first rule above. "Score every mention" becomes "score every post, with per-entity outcomes attached."
- `05` sample size: effective N is now computed from `w`, so low-`c` rows count for less. Recompute the d versus N budget after the first `c` distribution is known.
- Multi-entity posts: one post can carry several entities. Default: take the mean `p` weighted by mention prominence (title over body), keep per-entity rows for diagnostics. Open item below.

## Open items

1. Multi-entity rule: mean weighted by prominence, or max, or split into one training row per entity?
2. Whether comments are rows of their own (`14` open item). Same schema would apply.
3. Whether type C posts get any post-effect label for a separate "attention" model, or are simply excluded from training.
4. Initial `q` factor values. Placeholder until the first gold set exists.
