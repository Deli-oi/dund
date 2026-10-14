# 39 - Live input contract

Status: Current. Written October 14, 2026. Implements D12 (and relies on D2, D9, D13) of `38`. Code: `src/dund/featurespec.py`. No measured numbers appear here; every threshold is a default the user may change.

The rule: a post pulled live must become exactly the same input vector the model saw in training and test, or the scorer refuses.

## 1. The path (follow it in order)

1. **Raw record.** The live collector emits the same raw record shape as the census dump. Checklist: same field names, UTC timestamps, no author names beyond what `to_item` hashes (`DUND_SALT` set, D13).
2. **`to_item(raw, transform_version)`** (`transform.py`). Same function, same `transform_version` as the bundle. Feature view is the allowlist `Item.feature_view()` (D9). Never feed score, comment count, flair, `edited`, `removed_*`.
3. **Resolver.** Same resolver code and the same point-in-time ticker table (hash recorded in the bundle). Candidates come from `resolver.resolve(title, body, url)`.
4. **Ticker-day aggregation.** Same `TickerDayAggregator`, fed items in time order. A day is finalized only at the decision time (00:00 UTC next day, D2). Posts after it belong to the next ticker-day.
5. **Vectorize.** `FeatureSpec.vectorize(row)` enforces column order and dtype; it raises on unknown or missing columns. Missing values become the explicit marker declared per column, never a silent zero.
6. **Check hash, then score.** `spec.check(bundle.spec_hash)` runs before the model is touched.

## 2. What is identical and what cannot be

Identical by construction: `to_item`, resolver, aggregation function, column order, dtype, encoding, missing rules, decision-time rule, `transform_version`.

Cannot be identical (documented, not hidden):

| Difference | Effect | Handling |
|---|---|---|
| Capture lag (about 21 s, `retrieved_lag_s`) | Live sees a post slightly later than its creation; a post may be missing if removed within the lag | Record `retrieved_lag_s`; report share of posts above the lag default |
| Bodies already removed at capture | Text empty or placeholder; title-only share rises | `title_only_frac` is a feature, so shift shows in drift; report by removed status (D11) |
| No future prices | Labels do not exist at decision time | Live calls are scored later with the same rule (`37` section 4); price never enters features |
| Trailing-window features (`prior_30d_posts`, `prior_90d_posts`, `first_seen_in_set`) | Need history that a fresh process does not have | Rolling store of the last 90 days of finalized ticker-day state, seeded from the census, persisted between runs. If the store is incomplete, the column is the declared missing marker and the report says so |
| Ticker table version | Current snapshot differs from training table | Bundle stores the table hash; a different table is a different resolver version and fails the check unless re-trained or explicitly waived in the report |
| Decision time | Same-day reaction excluded (D2) | Live scoring runs only after 00:00 UTC; no intraday scoring in the default |
| Edited posts | Text may contain later outcomes | Flagged live and dropped from features (D9) |

## 3. Frozen model bundle

Stored together, immutable, in one directory:

- model file (format is model-specific; spec is not)
- `feature_spec.json` (`FeatureSpec.to_json()`)
- `spec_hash` (sha256 of the spec JSON)
- `transform_version`
- ticker table hash (and resolver version)
- training data snapshot id (`data_snapshot_id`)
- calibration table (mapping score to calibrated probability, and the interval method)
- training feature distributions (bin edges and shares per feature) for PSI
- `p_be` and flag cutoff as fixed from the validation block (D1)

## 4. Scorer refusal rules

The scorer stops and writes a refusal into the report (no partial score) when:

1. `spec_hash` of the loaded spec differs from the bundle's.
2. `transform_version` of produced items differs from the spec's.
3. Ticker table hash differs and no waiver is recorded.
4. `vectorize` raises: unknown column, missing column, wrong dtype, non-finite float, or a missing value in a column whose rule is `error`.
5. Rolling store has a gap in the last 90 days larger than the default tolerance (**PARAMETER**, suggested 1 day) and the affected columns have no marker rule.
6. `DUND_SALT` not set.
7. Items arrive out of time order (aggregator already raises).
8. Parity test has not passed for this code version (section 8).

An individual ticker-day may be abstained (not refused) when its row is degraded; the abstain count appears in the report denominators (`18` rule 4).

## 5. Drift monitoring

Computed per live report against the bundle's training distribution:

| Monitor | Definition |
|---|---|
| PSI per feature | Population stability index over training-time bins |
| Sub mix | Share of posts per subreddit vs training share (PSI on the mix) |
| Resolved share | Posts with at least one stock candidate / posts scanned |
| Unobservable share | Share of flagged ticker-days without a valid price series (D10) |

Suggested defaults (**PARAMETER**, conventional rules of thumb, not validated here): PSI below 0.10 normal, 0.10 to 0.25 warn, above 0.25 alert. Resolved or unobservable share moving more than a fixed band from training (suggested 5 percentage points) is a warn. An alert on any feature or on sub mix downgrades all `ACT` to `WATCH` in that report until reviewed.

## 6. Failure modes and what the report says

| Failure | Report text (verbatim intent) |
|---|---|
| Spec or version mismatch | "Run refused: input format differs from the frozen model (spec hash mismatch). No scores produced." |
| Rolling store incomplete | "Trailing-window features degraded for N ticker-days; marked missing; ACT disabled for them." |
| Capture gap or lag spike | "Collector gap of X; posts in the gap are absent; counts for affected days are lower bounds." |
| Bodies removed | "Share of title-only posts is X vs Y in training." |
| Ticker table changed | "Resolver version differs from training; results not comparable." |
| Drift alert | "Feature F PSI above alert default; ACT downgraded to WATCH." |
| No outcome yet | "Calls are unscored until the window closes; no hit rate for this period." |

Every report states the denominators (scanned, resolved, scored, abstained, refused), the bundle id, spec hash and `transform_version`.

## 7. Versioning and re-training triggers

- Any change to a column, encoding, missing rule, resolver, ticker table, `transform_version` or decision rule changes the spec hash; it is a new spec, never an overwrite.
- A new spec requires a new bundle (re-train, re-calibrate). Old bundles stay readable and are not deleted.
- Re-train or re-validate when: the spec hash must change; PSI alert persists for a fixed number of consecutive reports (**PARAMETER**, suggested 4); ticker table is refreshed; resolved share leaves the band; live calibration (on closed windows) departs from the calibration table beyond its interval.

## 8. Test plan

1. **Spec unit tests** (`tests/test_featurespec.py`): hash stability and sensitivity, order, unknown or missing column, missing marker, dtype, parity pass and fail.
2. **Parity test (CI and before every weekly report):** take a sample of raw census posts; path A is the census build, path B is the live-collector-shaped adapter (raw record, `to_item`, resolver, aggregator, in a fresh process with the rolling store seeded from earlier days). `assert_parity(rows_a, rows_b, spec)` must pass; the first differing column is reported.
3. **Out-of-order and boundary tests:** a post at exactly 00:00 UTC and one second either side lands in the correct ticker-day.
4. **Rolling store test:** cold start, warm start and gap each give the declared values or markers.
5. **Refusal tests:** each rule in section 4 produces a refusal, not a score.
6. **Allowlist test:** no field outside `feature_view()` reaches the vector (D9).
7. **Drift test:** a synthetic shifted sample triggers the PSI alert; the training sample does not.
8. **End-to-end replay:** replay a past period through the live path and compare vectors with the training table before the first real live run.
