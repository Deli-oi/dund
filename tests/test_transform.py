import gzip
import json
from dataclasses import fields

import pytest

from dund.schema import SCORE_FIELD_NAMES
from dund.transform import iter_census, to_item

RAW = {
    "id": "abc", "created_utc": 1700000000, "retrieved_on": 1700003600,
    "subreddit": "stocks", "subreddit_subscribers": 1000, "author": "bob",
    "author_created_utc": 1600000000, "title": "Hello", "selftext": "Body",
    "url": "https://x.com/a", "domain": "x.com", "is_self": False,
    "link_flair_text": "DD", "score": 5, "ups": 5, "upvote_ratio": 0.9,
    "num_comments": 2, "num_crossposts": 0, "edited": 1700000100.0,
    "removed_by_category": None,
}


@pytest.fixture(autouse=True)
def salt(monkeypatch):
    monkeypatch.setenv("DUND_SALT", "test-salt")


def test_basic():
    it = to_item(RAW, "v1")
    assert it.text == "Hello\n\nBody"
    assert it.retrieved_lag_s == 3600
    assert it.created_at.tzinfo is not None
    assert it.author_hash and len(it.author_hash) == 64 and "bob" not in it.author_hash
    assert it.item_type == "post" and it.source == "reddit"


def test_missing_salt_errors(monkeypatch):
    monkeypatch.delenv("DUND_SALT")
    with pytest.raises(RuntimeError, match="DUND_SALT"):
        to_item(RAW, "v1")


def test_removed_and_deleted():
    r = dict(RAW, selftext="[removed]", author="[deleted]", removed_by_category="moderator")
    it = to_item(r, "v1")
    assert it.text == "Hello" and it.author_hash is None
    assert it.removed_flag and it.removed_by_category == "moderator"


def test_missing_keys_and_edited_bool():
    it = to_item({"id": "z", "created_utc": 5, "edited": False}, "v1")
    assert it.author_created_utc is None and it.retrieved_lag_s is None
    assert it.subreddit_subscribers is None and it.text == ""
    to_item(dict(RAW, edited=True), "v1")


def test_parity_census_vs_live(tmp_path):
    p = tmp_path / "s_2023-11.jsonl.gz"
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(RAW) + "\n\n")
    census = to_item(next(iter_census(p)), "v1")
    live = {k: RAW[k] for k in reversed(list(RAW))}
    live["extra_live_key"] = "x"
    live["score_at_1h"] = 3
    assert to_item(live, "v1") == census


def test_no_score_leak():
    it = to_item(RAW, "v1")
    view = it.feature_view()
    assert "raw_score_fields" not in view
    assert not set(SCORE_FIELD_NAMES) & set(view)
    assert set(view) <= {f.name for f in fields(it)} | {"hour_utc", "weekday", "author_age_days"}


def test_feature_view_is_allowlist():
    import dataclasses
    from dund.schema import FEATURE_ALLOWLIST
    it = to_item(RAW, "v1")
    view = it.feature_view()
    for bad in ("removed_flag", "removed_by_category", "flair", "subreddit_subscribers",
                "edited_flag", "raw_score_fields", "author_hash", "retrieved_lag_s"):
        assert bad not in view
    assert not set(SCORE_FIELD_NAMES) & set(view)
    # a brand-new Item field is not exposed unless allowlisted
    Sub = dataclasses.make_dataclass("Sub", [("new_field", int, 1)], bases=(type(it),), frozen=True)
    sub = Sub(**{f.name: getattr(it, f.name) for f in fields(it)})
    assert "new_field" not in sub.feature_view()
    assert set(FEATURE_ALLOWLIST) <= set(view)


def test_edited_flag_and_is_trainable():
    from dund.transform import is_trainable
    assert to_item(RAW, "v1").edited_flag is True
    assert not is_trainable(to_item(RAW, "v1"))
    ok = to_item({"id": "a", "created_utc": 5, "title": "hi", "edited": False}, "v1")
    assert ok.edited_flag is False and is_trainable(ok)
    empty = to_item({"id": "b", "created_utc": 5, "title": "[removed]"}, "v1")
    assert not is_trainable(empty)
