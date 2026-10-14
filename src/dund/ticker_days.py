"""Ticker-day aggregator: one row per (stock ticker, UTC date).

Items must be fed in non-decreasing UTC-date order (single pass). Prior-mention
counts use only strictly earlier days, so there is no look-ahead. Repo candidates
go to a separate table. Cluster key for inference is the ticker.

Timestamp semantics (docs/38 D2): a row covers all posts of one UTC date `date`.
`decision_ts` = 00:00 UTC of the NEXT day (ISO, end of that UTC day); every feature uses
only posts created on `date`, i.e. at or before decision_ts. `first_post_ts` is an audit
field only. `audit_removed_frac` is audit/selection-bias reporting, never a feature (D9).
Each item_id is counted once per day (duplicates are dropped).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

TICKER_DAY_FIELDS = [
    "ticker", "date", "decision_ts", "n_posts", "n_authors", "subs_json", "n_subs", "first_post_ts",
    "title_only_frac", "audit_removed_frac", "first_seen_in_set", "prior_30d_posts",
    "prior_90d_posts", "top_author_share", "max_confidence", "cluster_key",
]
REPO_FIELDS = ["repo", "date", "n_posts", "n_authors", "subs_json", "first_post_ts"]


def utc_date(dt: datetime) -> date:
    return dt.astimezone(timezone.utc).date()


def split_text(text: str):
    title, _sep, body = text.partition("\n\n")
    return title, body


class _Acc:
    __slots__ = ("n", "authors", "subs", "first_ts", "title_only", "removed", "maxconf")

    def __init__(self):
        self.n = 0
        self.authors = Counter()
        self.subs = Counter()
        self.first_ts = None
        self.title_only = 0
        self.removed = 0
        self.maxconf = 0.0

    def add(self, item, conf, title_only):
        self.n += 1
        if item.author_hash:
            self.authors[item.author_hash] += 1
        self.subs[item.subreddit] += 1
        if self.first_ts is None or item.created_at < self.first_ts:
            self.first_ts = item.created_at
        self.title_only += title_only
        self.removed += bool(item.removed_flag)
        self.maxconf = max(self.maxconf, conf)


class TickerDayAggregator:
    def __init__(self, resolver):
        self.resolver = resolver
        self.stats = {
            "posts": Counter(),            # (sub, year) -> posts
            "resolved": Counter(),         # (sub, year) -> posts with >=1 stock candidate
            "mentions_by_year": defaultdict(Counter),   # year -> ticker -> posts
            "tickerdays_by_year": Counter(),
            "tickerdays_by_sub_year": Counter(),
            "tickers_by_year": defaultdict(set),
        }
        self._cur_day = None
        self._stock = {}
        self._repo = {}
        self._hist = {}     # ticker -> {date: n_posts} (finalized days only)
        self._seen = set()
        self._day_ids = set()   # item ids already counted on the current day

    def add(self, item):
        """Feed one item; returns (ticker_rows, repo_rows) finalized by this call."""
        d = utc_date(item.created_at)
        if self._cur_day is not None and d < self._cur_day:
            raise ValueError(f"items out of time order: {d} after {self._cur_day}")
        out = ([], [])
        if self._cur_day is not None and d > self._cur_day:
            out = self._flush()
        self._cur_day = d
        if item.item_id in self._day_ids:
            return out
        self._day_ids.add(item.item_id)
        title, body = split_text(item.text)
        title_only = 0 if body else 1
        cands = self.resolver.resolve(title, body, item.url or "")
        key = (item.subreddit, d.year)
        self.stats["posts"][key] += 1
        stock = False
        for c in cands:
            if c.entity_type == "stock":
                stock = True
                self._stock.setdefault(c.id, _Acc()).add(item, c.confidence, title_only)
            elif c.entity_type == "repo":
                self._repo.setdefault(c.id, _Acc()).add(item, c.confidence, title_only)
        if stock:
            self.stats["resolved"][key] += 1
        return out

    def finish(self):
        if self._cur_day is None:
            return [], []
        return self._flush()

    def _flush(self):
        d = self._cur_day
        trows, rrows = [], []
        for tk in sorted(self._stock):
            a = self._stock[tk]
            hist = self._hist.setdefault(tk, {})
            p30 = sum(n for dd, n in hist.items() if d - timedelta(days=30) <= dd < d)
            p90 = sum(n for dd, n in hist.items() if d - timedelta(days=90) <= dd < d)
            for dd in [x for x in hist if x < d - timedelta(days=90)]:
                del hist[dd]
            hist[d] = a.n
            first = tk not in self._seen
            self._seen.add(tk)
            top = max(a.authors.values()) / a.n if a.authors else 0.0
            trows.append({
                "ticker": tk, "date": d.isoformat(),
                "decision_ts": (datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
                                + timedelta(days=1)).isoformat(),
                "n_posts": a.n,
                "n_authors": len(a.authors),
                "subs_json": json.dumps(dict(sorted(a.subs.items())), separators=(",", ":")),
                "n_subs": len(a.subs),
                "first_post_ts": a.first_ts.astimezone(timezone.utc).isoformat(),
                "title_only_frac": a.title_only / a.n, "audit_removed_frac": a.removed / a.n,
                "first_seen_in_set": int(first), "prior_30d_posts": p30,
                "prior_90d_posts": p90, "top_author_share": top,
                "max_confidence": a.maxconf, "cluster_key": tk,
            })
            s = self.stats
            s["mentions_by_year"][d.year][tk] += a.n
            s["tickerdays_by_year"][d.year] += 1
            s["tickers_by_year"][d.year].add(tk)
            for sub in a.subs:
                s["tickerdays_by_sub_year"][(sub, d.year)] += 1
        for repo in sorted(self._repo):
            a = self._repo[repo]
            rrows.append({
                "repo": repo, "date": d.isoformat(), "n_posts": a.n,
                "n_authors": len(a.authors),
                "subs_json": json.dumps(dict(sorted(a.subs.items())), separators=(",", ":")),
                "first_post_ts": a.first_ts.astimezone(timezone.utc).isoformat(),
            })
        self._stock, self._repo = {}, {}
        self._day_ids = set()
        return trows, rrows


def aggregate(items: Iterable, resolver) -> tuple:
    """Convenience: returns (ticker_rows, repo_rows, aggregator)."""
    agg = TickerDayAggregator(resolver)
    t, r = [], []
    for it in items:
        a, b = agg.add(it)
        t += a
        r += b
    a, b = agg.finish()
    return t + a, r + b, agg
