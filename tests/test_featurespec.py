import pytest
from dund.featurespec import (Column, FeatureSpec, SpecError, SpecHashMismatch,
                              ParityError, assert_parity)


def make(cols=None):
    cols = cols or (Column("n_posts", "int"),
                    Column("share", "float", missing="marker", marker=-1.0),
                    Column("sub", "str"))
    return FeatureSpec(tuple(cols), "tv1", "tickers-2026-10")


def test_hash_stable_and_roundtrip():
    s = make()
    assert s.spec_hash == make().spec_hash
    assert FeatureSpec.from_json(s.to_json()).spec_hash == s.spec_hash


def test_hash_changes_on_edits():
    base = make().spec_hash
    c = list(make().columns)
    assert make([c[1], c[0], c[2]]).spec_hash != base
    assert make([Column("n_posts", "float"), c[1], c[2]]).spec_hash != base
    assert make([Column("n_post", "int"), c[1], c[2]]).spec_hash != base
    assert make([Column("n_posts", "int", encoding="log1p"), c[1], c[2]]).spec_hash != base
    assert FeatureSpec(tuple(c), "tv2", "tickers-2026-10").spec_hash != base


def test_check():
    s = make()
    s.check(s.spec_hash)
    with pytest.raises(SpecHashMismatch):
        s.check("0" * 64)


def test_order_enforced():
    assert make().vectorize({"sub": "a", "share": 0.5, "n_posts": 3}) == [3, 0.5, "a"]


def test_unknown_and_absent():
    s = make()
    with pytest.raises(SpecError):
        s.vectorize({"n_posts": 1, "share": 0.1, "sub": "a", "x": 1})
    with pytest.raises(SpecError):
        s.vectorize({"n_posts": 1, "sub": "a"})


def test_missing_marker_and_error():
    s = make()
    assert s.vectorize({"n_posts": 1, "share": None, "sub": "a"})[1] == -1.0
    with pytest.raises(SpecError):
        s.vectorize({"n_posts": None, "share": 0.1, "sub": "a"})


def test_dtype_enforced():
    with pytest.raises(SpecError):
        make().vectorize({"n_posts": "3", "share": 0.1, "sub": "a"})
    with pytest.raises(SpecError):
        make().vectorize({"n_posts": 1, "share": float("nan"), "sub": "a"})


def test_parity():
    s = make()
    r = {"n_posts": 1, "share": 0.5, "sub": "a"}
    assert assert_parity([r], [dict(reversed(list(r.items())))], s) == 1
    with pytest.raises(ParityError, match="share"):
        assert_parity([r], [dict(r, share=0.6)], s)
    with pytest.raises(ParityError):
        assert_parity([r], [r, r], s)
