# 14 - Data collection deep dive

Written October 13, 2026 after the switch to the public Reddit history repo as the training source (`07`, `11`). This audits `11` and `04` and proposes changes. Nothing here has been run. Items marked (measure) are open until a real count exists. I have not yet seen the Reddit repo's schema, so every claim about its fields is an assumption to check at stage R0.

## Verdict

The old runbook was built repo-first (GH Archive finds emerging repos, Reddit is an optional reader). With Reddit history as the training source the unit becomes a **mention of a repo in a post**, and four things in `11` and `04` no longer fit: candidate generation, cohort definition, the feature list, and the leakage story. The sections below list what to change and how to keep the pipeline cheap to change as the data teaches us things.

## 1. What the new data can and cannot give us

| Question | Why it matters | How to settle it |
|---|---|---|
| What fields exist per post (id, created_utc, subreddit, author, title, selftext, url, score, num_comments, removed/deleted flags, edit time)? | Decides which features are possible | R0 profile of one month |
| Is score/num_comments final or ingestion-time? | `04` already warns fresh posts carry score 1 | Plot `retrieved_on - created_utc` by month |
| Are comments included, and do they carry links? | Comments are a large share of repo mentions and a second source of "first mention" | R0 profile |
| How complete is each year? Gaps, removals, deleted authors | Missing months create fake "first mentions" and fake negatives | Posts per sub per month curve |
| How does the share of posts with a GitHub link move over time? | Regime changes (2023 API changes, blackouts, bots) | Monthly series |

**Consequence:** the model's features must be limited to what the dump has at post time. Early dynamics (score at 1h, 6h) exist only for live collection. Define two feature sets and never mix them: **dump-compatible** (trains and evaluates historically) and **live-only** (collected going forward, usable only after enough live history accumulates).

## 2. Changes to candidate generation

> Updated: `16` makes the post the input row. R1 to R5 below still apply as the entity-resolution and outcome steps, but their output attaches to posts rather than defining the rows.

Old: GH Archive finds repos with at least 5 stars in 30 days (S1). Problem: that filter uses information after the mention and selects on the outcome.

New:

1. **R1. Mention extraction.** From posts (and optionally comments) in seed and discovered subs, extract GitHub URLs. Normalize `github.com/owner/name`, strip paths, `.git`, `www`, and case. Record post id, timestamp, subreddit, author, link position (url field vs selftext vs comment).
2. **R2. Resolve to repo id.** Join to GH Archive (or API) by repo name at mention time, then store the numeric repo id. Names get renamed and transferred, and ids do not. Unresolvable links are kept in a `dropped` table with a reason, not silently removed.
3. **R3. First mention.** First mention per repo id across all scanned subs, defined by timestamp. Because the dump only covers the subs we scan, "first mention" is first within the scanned set. Record that limitation as a field (`scanned_subs_version`).
4. **R4. Eligibility filter that uses only pre-mention information.** For example: repo created before the mention, repo age at mention at most N days, not a fork, not owned by the poster's company if known. No filter on later stars.
5. **R5. Control set.** Repos never mentioned in the scanned subs, sampled from GH Archive with matched age and star count at the same date. This answers the question that matters: does Reddit add anything beyond what the repo's own early curve already says (K2 in `13`, baselines in `12`).

## 3. Leakage and causality problems specific to a Reddit-trained model

- **The post can cause the outcome.** A post in a big sub drives stars directly. The model may learn "big sub plus repo link equals growth" rather than anything early or clever. Mitigation: report results with and without subreddit size features, and compare mentions in large vs small subs after matching on repo stars at T.
- **Selection into mention.** Repos get posted when their owners promote them. Author equals owner is a feature, but also a stratum to report separately.
- **Stars at T.** The repo's star count and 7-day growth before T are strong, honest features and must be in the model from day one. If Reddit features do not beat that baseline, the result is "Reddit adds nothing," which is a valid finding.
- **Later mentions** (count, citations) are label-side only (`04`). Enforce by a column prefix (`label_`, `feat_`) checked in CI.
- **Duplicate and cross-posted links.** The same repo posted in 5 subs within hours is one event. Group by repo id and a short window, and count cross-posts as a feature only if known at T.
- **Fake stars.** GitHub star inflation by paid or bot accounts is documented since about 2023. Flag repos with abnormal star burst plus low-activity accounts (GH Archive actor age and event counts). Flag, do not delete, and report results with and without them.
- **Unstars and deletions** are not in the archive. Star counts from the archive are cumulative stars given, not current stars. State this once and use the same definition everywhere.

## 4. Label and cohort decisions that need a real count first

`11` S4 uses top 5% of the same-month cohort on 12-month star gain. With mentions as the unit:

- **Cohort option A:** repos first mentioned in the same month in the scanned subs. Small cohorts in early years, and "top 5%" is a statement about Reddit-mentioned repos only.
- **Cohort option B:** all repos of similar age and star count at T (from GH Archive). Larger, cleaner, and measures "better than similar repos," but needs the R5 machinery.
- **Recommendation:** compute both labels and report which one the features predict better. Pick A as the primary only if cohort sizes allow (at least 30 per cell), otherwise B.
- **Absolute and relative outcomes** both go in the table (raw 12-month gain, percentile within cohort, log gain). The label is a choice made later from stored values, not at pull time.
- **Horizons** 3, 12, and 24 months computed from the same curves. Right-censored rows kept with a censor flag.

## 5. Make it adjustable: how to change inputs without breaking science

You said inputs will change as the data shows trends. That is expected, but each change spends test-set credibility. Design for cheap change and honest accounting:

**Storage (cheap to change)**

- **Keep a raw filtered layer.** For scanned subs, keep the full post (and comment, if used) rows needed to recompute any text, link, or author feature later, in Parquet. Estimate size at R0 (measure). If the layer is too big for 40 GB, keep it on the laptop or a cheap volume, not on the VPS.
- **Immutable, versioned snapshots.** Each pull writes `data/<layer>/<version>/` with a manifest: source commit and checksum, code git SHA, parameters, row counts, date. Nothing is overwritten.
- **Join keys are ids, never names.** Repo id, post id, author id (hashed per `11` rule 6).

**Features (cheap to change)**

- **Feature registry** (`features.yaml`): name, definition, available-at rule (e.g., "T", "T plus 1h"), source layer, compatible set (dump or live), version, owner, leakage-test status. A model run takes a list of registry names. A feature cannot enter a model unless its available-at rule passes the automated leakage check.
- **One feature set per model version,** recorded in the run manifest with the data snapshot ids.

**Process (honest to change)**

- **Auto data profile after every pull** (counts per month and sub, missingness, link share, positive rate per month, feature distributions, drift versus last pull). You read it before any modelling. Proposed changes to inputs get logged in `07` as dated decisions with the evidence.
- **Trial counter.** Each distinct feature set, label definition, or filter change evaluated against validation folds increments the counter (`12`). Test years are touched only at the end of a pre-declared round, and the number of rounds is declared in advance.
- **Ablation before addition.** New inputs enter in groups (link flags, subreddit stats, author history, text embedding, event context). Each group is scored by walk-forward ablation, and kept only if it improves out-of-time performance beyond its bootstrap interval.
- **Discovery loop for subreddits.** New subs get added through the `11` S1 criteria and tagged `added_at`, so training can reproduce "what the scanner knew at the time" and not use subs found only after seeing outcomes.
- **Drift triggers.** If a feature's monthly mean moves more than a set number of standard deviations, or positive rate shifts, the profile flags it and the half-life grid (`04`) is rerun.

## 6. Quality checks before modelling (proposed gates)

| Check | Pass condition (placeholder) |
|---|---|
| Entity resolution audit: hand-check 100 random extracted links | At least 95% correct repo id; recall estimated on 100 random posts with links |
| Coverage: posts per sub per month vs known volume | No unexplained gaps over 2 consecutive months |
| Positive count | At least about 300 raw positives under the chosen definition (`11` G2). If fewer, widen subs, relax top-5% to top-10%, or lengthen the window |
| Effective N vs feature count | Per `05`: features limited to roughly N_eff / 20 |
| Label sanity | Known famous repos (hand list of about 30 from the period) sit in the top bins; known duds do not |
| Leakage suite (T2) on real data | Fails the build on an injected label-side feature and on shuffled labels |
| Baseline | Repo-only baseline (stars at T, 7-day growth, age, owner type) computed first. Reddit features must beat it out of time |

## 7. Revised stage order

| Stage | What | Gate |
|---|---|---|
| R0 | Profile the Reddit repo: schema, coverage, field semantics, size, license text recorded. One month first | You review the profile |
| R1-R3 | Extract mentions, resolve to repo ids, first-mention table | Entity audit (6) |
| S1' | Pull GH Archive curves for resolved repo ids and the matched control set (R5), reduced Parquet | G1 cost, G2 positive count |
| S2-S4 | Features at T, outcomes after T, labels (both cohort options), confounder flags | G4 leakage |
| S3 | HN attention (unchanged) | |
| B0 | Repo-only baseline | Must exist before any Reddit feature is evaluated |
| M1 | Dump-compatible model, then ablations | Trial counter |
| L1 | Live collector for early-dynamics features, running from now (start early, accumulates) | |

## 8. Open items I need from you

1. The repo URL (R0 cannot start without it), and where to run it (laptop disk vs VPS).
2. Whether comments are in scope for mentions, or posts only. Comments multiply volume and size.
3. Which cohort option (A or B in section 4) you prefer as primary, or whether to let the first counts decide.
4. Whether to include non-seed subs found by link-based discovery (e.g., any sub where GitHub links appear often) from the start, or only the seed list. The first widens the data and the bias risk together.
