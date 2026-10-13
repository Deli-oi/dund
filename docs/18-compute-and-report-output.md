# 18 - Compute placement and the final report

Decision of October 13, 2026 (Eli): run everything on the current laptop, use cloud only for what it cannot hold. The agentic output is a report that says what to do and how far above the threshold each call was. Supersedes "Where things run" in `11` and the VPS framing in `01`.

## What the laptop has (measured today)

| Resource | Value | Consequence |
|---|---|---|
| Free disk on C: | **about 3 GB** (472 GB used) | The laptop cannot hold the dataset, raw or filtered, and barely holds the repo, Python env, and a few Parquet files |
| RAM | about 31 GB | Fine for modelling and for streaming one month at a time |
| CPU | Ryzen 5 Pro 7535U, no discrete GPU | Fine for logistic regression and Parquet work. Not for large embeddings |
| Project path | Inside Dropbox | **Keep data out of Dropbox.** Sync would try to upload it. Code and docs only in the Dropbox folder, or move the repo out of it |

Free space has to be freed or an external drive added before any local data work. Check the free space again before relying on this number.

## Placement rule

| Work | Where | Why |
|---|---|---|
| Code, docs, tests, small tables (under about 1 GB), model fitting, reports, dashboards | Laptop | Fits, and no cloud cost |
| Torrent download, month-by-month filtering of the 3.8 TB archive, GH Archive reductions | Cloud, temporary | Needs hundreds of GB of scratch for hours or days |
| Reduced Parquet (seed subs, resolved entities, outcomes) | Cloud object storage, synced down on demand | Estimated tens of GB (measure at R0). If under about 2 GB per model dataset, pull the working subset to the laptop |
| Scheduled live collectors | Cloud VM (small) | Laptop is not always on |
| Anything that spends model tokens | Laptop agent session | No LLM agent on the server (`11`) |

## Cloud approach (cheap, temporary)

- One short-lived VM with a large volume, created for the ingest, destroyed afterward. Stream: torrent file for a month, filter to scanned subs, write reduced Parquet, delete the raw month. Disk need is a few months of raw at a time, not 3.8 TB.
- If torrent file selection is not possible, use the Arctic Shift per-subreddit tool or API (limits to verify) instead.
- Before buying anything: re-estimate cost from the R0 profile. The $200 build budget in `10` stands. Rough cost shape (verify prices): a mid-size VM plus a few hundred GB volume for days is single or low double digits of dollars, while holding the full 3.8 TB on a volume for weeks is likely hundreds. Do not do that.
- Everything downloaded goes in its own empty directory and is treated as untrusted data.

## The final output: an action report with margin over threshold

One report per run (daily or weekly), produced by the agent from model outputs only. **It does not trade.** Paper only (`10`).

### Per flagged item

| Field | Meaning |
|---|---|
| Action | `ACT` (paper position), `WATCH` (near threshold), `SKIP` (below). Abstain is a first-class outcome |
| Asset and post | Ticker or token, subreddit, post id, timestamp, lead time estimate |
| `p` | Calibrated probability the post is an early signal of a market shift (`17`) |
| Interval | Lower and upper bound (bootstrap or conformal, `04`) |
| Threshold `p*` | Decision threshold from the risk rule (`10`), recorded with the payoff scenario used |
| **Margin** | `p_lower - p*`, in percentage points. Positive means the lower bound clears the bar |
| Margin z | `(p - p*) / se`, so a reader sees how many standard errors above the bar |
| Reason codes | Top contributing features, and what lowered confidence (resolution, thin data, confounder risk) |
| Sizing note | Paper size under the gates in `10`, with the drawdown state |
| Model and label version | `label_version`, model id, data snapshot id |

### Rules

1. **Rank by margin, not by `p`.** A high `p` with a wide interval ranks below a moderate `p` with a tight one.
2. **`ACT` only when margin is above zero** after calibration, and the item is not confounded, illiquid, or from a regime the model flags as out of distribution.
3. **`WATCH`** lists items whose point estimate clears the threshold but whose lower bound does not, with the margin as a negative number. This is the review queue for hand labels (`16`).
4. **Report the denominators:** number of posts scanned, number scored, number abstained, and how many of last period's `ACT` items resolved as hits, with intervals. No cherry-picking.
5. **Truth board numbers** (trial counter, luck meter, `12`) appear on the front page so a good-looking week is not mistaken for skill.
6. **Not advice.** The report states it is a research output on paper trades.

### Example row (invented numbers)

| Action | Asset | Post | p | Interval | p* | Margin | z |
|---|---|---|---|---|---|---|---|
| ACT | XYZ | r/sub, 2026-10-12 | 0.81 | 0.74 to 0.87 | 0.70 | +4 pp | +2.1 |
| WATCH | ABC | r/sub, 2026-10-12 | 0.74 | 0.63 to 0.82 | 0.70 | -7 pp | +0.8 |

## Open items

1. Free local disk: clear space, add an external drive, or move the repo out of Dropbox (required for local data).
2. Cloud provider and spend cap. Default plan is a short-lived Hetzner or similar VM, but nothing is bought without you.
3. Report cadence (daily or weekly) and delivery (file in the repo, email draft, or artifact).
4. The payoff scenario that sets `p*` (default G = L = 100%, so `p*` = 0.70 with the +0.20 safety margin, `07`).
