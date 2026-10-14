"""The single raw -> Item transform, used for census files and live input."""
from __future__ import annotations

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from .schema import SCORE_FIELD_NAMES, Item, hash_author

_PLACEHOLDERS = {"[removed]", "[deleted]"}


def _clean_str(v: Any) -> str:
    if not isinstance(v, str):
        return ""
    return "" if v.strip() in _PLACEHOLDERS else v


def _opt_str(v: Any) -> Optional[str]:
    return v if isinstance(v, str) and v != "" else None


def _opt_int(v: Any) -> Optional[int]:
    if v is None or isinstance(v, bool):
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def to_item(raw: dict, transform_version: str, salt: Optional[str] = None) -> Item:
    created = _opt_int(raw.get("created_utc"))
    if created is None:
        raise ValueError("record has no created_utc")
    item_id = raw.get("id")
    if not item_id:
        raise ValueError("record has no id")
    retrieved = _opt_int(raw.get("retrieved_on"))
    author = raw.get("author")
    if not isinstance(author, str) or author.strip() in _PLACEHOLDERS:
        author = None
    title = _clean_str(raw.get("title"))
    body_raw = raw.get("selftext")
    body = _clean_str(body_raw)
    text = (title + "\n\n" + body) if body else title
    rbc = _opt_str(raw.get("removed_by_category"))
    removed = bool(rbc) or (isinstance(body_raw, str) and body_raw.strip() == "[removed]")
    # `edited` may be bool or timestamp; it is not part of the schema (post-time unknowable).
    scores = {k: raw.get(k) for k in SCORE_FIELD_NAMES}
    return Item(
        source="reddit",
        item_id=str(item_id),
        created_at=datetime.fromtimestamp(created, tz=timezone.utc),
        subreddit=str(raw.get("subreddit") or ""),
        author_hash=hash_author(author, salt),
        text=text,
        url=_opt_str(raw.get("url")),
        domain=_opt_str(raw.get("domain")),
        is_self=bool(raw.get("is_self")),
        flair=_opt_str(raw.get("link_flair_text")),
        item_type="post",
        removed_flag=removed,
        removed_by_category=rbc,
        author_created_utc=_opt_int(raw.get("author_created_utc")),
        subreddit_subscribers=_opt_int(raw.get("subreddit_subscribers")),
        retrieved_lag_s=(retrieved - created) if retrieved is not None else None,
        transform_version=transform_version,
        raw_score_fields=scores,
    )


def iter_census(path) -> Iterator[dict]:
    """Stream raw records from one gzipped JSONL census file (blank lines skipped)."""
    with gzip.open(Path(path), "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)
