"""Canonical row schema. One Item shape for training (census) and live input."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Any, Dict, Optional

SALT_ENV = "DUND_SALT"
# Keys refreshed after post time. NEVER features (doc 19 group Y, doc 22 point 7).
SCORE_FIELD_NAMES = ("score", "ups", "upvote_ratio", "num_comments", "num_crossposts")


FEATURE_ALLOWLIST = ("text", "url", "domain", "is_self", "item_type", "subreddit",
                     "author_created_utc", "over_18")
# Derived (computed in feature_view): hour_utc, weekday, author_age_days.


def get_salt() -> str:
    salt = os.environ.get(SALT_ENV)
    if not salt:
        raise RuntimeError(
            f"Environment variable {SALT_ENV} is not set. Set it to the secret salt used "
            "to hash authors (tests: monkeypatch it)."
        )
    return salt


def hash_author(author: Optional[str], salt: Optional[str] = None) -> Optional[str]:
    if not author:
        return None
    s = salt if salt is not None else get_salt()
    return hashlib.sha256((s + "\x00" + author).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Item:
    source: str
    item_id: str
    created_at: datetime  # tz-aware UTC
    subreddit: str
    author_hash: Optional[str]
    text: str  # title + body
    url: Optional[str]
    domain: Optional[str]
    is_self: bool
    flair: Optional[str]
    item_type: str
    removed_flag: bool
    removed_by_category: Optional[str]
    author_created_utc: Optional[int]
    subreddit_subscribers: Optional[int]
    retrieved_lag_s: Optional[int]
    transform_version: str
    # NOT FEATURES: refreshed later, label-side only. Excluded from feature_view().
    raw_score_fields: Dict[str, Any] = field(default_factory=dict, compare=True)
    # AUDIT: True if the post was edited (text may include later outcomes). Never a feature.
    edited_flag: bool = False
    over_18: bool = False  # known at post time; allowlisted feature

    def feature_view(self) -> Dict[str, Any]:
        """Explicit ALLOWLIST of post-time-knowable fields (docs/38 D9). New Item fields
        are excluded until added to FEATURE_ALLOWLIST. Audit fields (removed_*, flair,
        subreddit_subscribers, edited_flag, scores, ...) stay on Item only."""
        out: Dict[str, Any] = {k: getattr(self, k) for k in FEATURE_ALLOWLIST}
        out["hour_utc"] = self.created_at.hour
        out["weekday"] = self.created_at.weekday()
        acu = self.author_created_utc
        out["author_age_days"] = (
            (self.created_at.timestamp() - acu) / 86400.0 if acu is not None else None)
        return out
