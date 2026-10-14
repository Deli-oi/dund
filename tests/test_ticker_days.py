import json
from datetime import datetime, timedelta, timezone

import pytest

from dund.entities import EntityResolver, TickerTable
from dund.schema import Item
from dund.ticker_days import ListFilterConfig, TickerDayAggregator, aggregate

R = EntityResolver(TickerTable.from_rows([("TSLA", "Tesla, Inc.", "1"), ("AAPL", "Apple Inc.", "2")]))


def item(i, ts, text, sub="stocks", author="a", removed=False):
    return Item("reddit", str(i), ts, sub, author, text, None, None, True, None, "post",
                removed, None, None, None, None, "t")


def utc(y, m, d, h=12, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


def rows(items):
    t, _, _ = aggregate(items, R)
    return {(r["ticker"], r["date"]): r for r in t}


def test_prior_counts_point_in_time():
    its = [item(0, utc(2020, 1, 1), "$TSLA up"), item(1, utc(2020, 1, 1, 13), "$TSLA up", author="b"),
           item(2, utc(2020, 1, 20), "$TSLA up"), item(3, utc(2020, 3, 30), "$TSLA up")]
    r = rows(its)
    assert r[("TSLA", "2020-01-01")]["prior_30d_posts"] == 0
    assert r[("TSLA", "2020-01-01")]["first_seen_in_set"] == 1
    assert r[("TSLA", "2020-01-20")]["prior_30d_posts"] == 2
    assert r[("TSLA", "2020-01-20")]["first_seen_in_set"] == 0
    assert r[("TSLA", "2020-03-30")]["prior_30d_posts"] == 0
    # Jan 1 is 89 days back, Jan 20 is 70 days back
    assert r[("TSLA", "2020-03-30")]["prior_90d_posts"] == 3


def test_no_lookahead():
    base = [item(0, utc(2020, 1, 1), "$TSLA"), item(1, utc(2020, 1, 5), "$TSLA")]
    extra = base + [item(2, utc(2020, 1, 9), "$TSLA")]
    assert rows(base)[("TSLA", "2020-01-05")] == rows(extra)[("TSLA", "2020-01-05")]


def test_same_day_across_subs():
    r = rows([item(0, utc(2020, 2, 3, 1), "$TSLA", sub="a", author="x"),
              item(1, utc(2020, 2, 3, 20), "$TSLA", sub="b", author="y", removed=True)])
    row = r[("TSLA", "2020-02-03")]
    assert row["n_posts"] == 2 and row["n_subs"] == 2 and row["n_authors"] == 2
    assert json.loads(row["subs_json"]) == {"a": 1, "b": 1}
    assert row["audit_removed_frac"] == 0.5 and row["title_only_frac"] == 1.0
    assert row["cluster_key"] == "TSLA"


def test_timezone_boundary():
    est = timezone(timedelta(hours=-5))
    late = datetime(2020, 2, 3, 20, 0, tzinfo=est)  # 2020-02-04 01:00 UTC
    items = sorted([item(0, late, "$TSLA"), item(1, utc(2020, 2, 3, 23, 59), "$TSLA"),
                    item(2, utc(2020, 2, 4, 0, 0), "$TSLA")], key=lambda i: i.created_at)
    r = rows(items)
    assert r[("TSLA", "2020-02-03")]["n_posts"] == 1
    assert r[("TSLA", "2020-02-04")]["n_posts"] == 2


def test_author_concentration_and_bodies():
    its = [item(0, utc(2020, 1, 1, 1), "$TSLA", author="a"),
           item(1, utc(2020, 1, 1, 2), "$TSLA\n\nbody text", author="a"),
           item(2, utc(2020, 1, 1, 3), "$TSLA", author="a"),
           item(3, utc(2020, 1, 1, 4), "$TSLA", author="b")]
    row = rows(its)[("TSLA", "2020-01-01")]
    assert row["top_author_share"] == 0.75 and row["n_authors"] == 2
    assert row["title_only_frac"] == 0.75


def test_repo_separate_and_order_enforced():
    t, rp, _ = aggregate([item(0, utc(2020, 1, 1), "see github.com/foo/bar")], R)
    assert t == [] and rp[0]["repo"] == "foo/bar"
    with pytest.raises(ValueError):
        aggregate([item(0, utc(2020, 1, 2), "$TSLA"), item(1, utc(2020, 1, 1), "$TSLA")], R)


def test_decision_ts_and_audit_fields():
    r = rows([item(0, utc(2020, 2, 3, 1), "$TSLA"), item(1, utc(2020, 2, 3, 23, 59), "$TSLA", author="b")])
    row = r[("TSLA", "2020-02-03")]
    assert row["decision_ts"] == "2020-02-04T00:00:00+00:00"
    assert row["first_post_ts"].startswith("2020-02-03T01:00")
    assert "removed_frac" not in row


def test_dedup_by_item_id():
    a = item(7, utc(2020, 2, 3, 5), "$TSLA")
    r = rows([a, a, item(8, utc(2020, 2, 3, 6), "$TSLA", author="b")])
    assert r[("TSLA", "2020-02-03")]["n_posts"] == 2


def test_build_script_requires_salt(monkeypatch, tmp_path):
    import importlib.util
    from pathlib import Path
    monkeypatch.delenv("DUND_SALT", raising=False)
    p = Path(__file__).resolve().parents[1] / "scripts" / "build_ticker_days.py"
    spec = importlib.util.spec_from_file_location("btd", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    (tmp_path / "in").mkdir()
    with pytest.raises(RuntimeError):
        m.main(str(tmp_path / "in"), str(tmp_path / "out"))


TICKS = [f"T{chr(65 + i // 26)}{chr(65 + i % 26)}" for i in range(150)]
RB = EntityResolver(TickerTable.from_rows([(t, f"Zzname{i} Corp", str(i)) for i, t in enumerate(TICKS)]))
QS = ["Q" + chr(65 + i // 26) + chr(65 + i % 26) for i in range(12)]
R_BIG = EntityResolver(TickerTable.from_rows(
    [("TSLA", "Tesla, Inc.", "1"), ("AAPL", "Apple Inc.", "2")]
    + [(t, f"Zzname{i} Corp", str(i + 10)) for i, t in enumerate(QS)]))


def test_list_post_creates_no_events_but_ordinary_does():
    big = " ".join("$" + t for t in TICKS)
    t, _, agg = aggregate([item(0, utc(2020, 1, 1), big, author="x")], RB)
    assert t == [] and agg.stats["list_post"][("stocks", 2020)] == 1
    t, _, _ = aggregate([item(1, utc(2020, 1, 1), "$TSLA $AAPL $TSLA", author="y")], R)
    assert {r["ticker"] for r in t} == {"TSLA", "AAPL"}


def _listposts(n, month, author="bot1", start=100):
    big = " ".join("$" + q for q in QS)
    return [item(start + i, utc(2020, month, 2 + i), big, author=author) for i in range(n)]


def test_bot_author_month_rule_and_no_lookahead():
    sept = [item(1, utc(2020, 9, 5), "$TSLA", author="bot1")]
    octo = [item(50, utc(2020, 10, 1), "$AAPL", author="bot1")] + _listposts(10, 10, start=200)
    nov = [item(900, utc(2020, 11, 3), "$TSLA", author="bot1"),
           item(901, utc(2020, 11, 3), "$TSLA", author="human")]
    t, _, agg = aggregate(sept + octo + nov, R_BIG)
    r = {(x["ticker"], x["date"]): x for x in t}
    assert ("TSLA", "2020-09-05") in r                 # September unaffected by October rule
    assert ("AAPL", "2020-10-01") not in r             # same-month earlier post excluded
    assert r[("TSLA", "2020-11-03")]["n_posts"] == 1   # bot excluded thereafter
    assert agg.stats["bot_post"][("stocks", 2020)] == 12
    t2, _, _ = aggregate([item(1, utc(2020, 10, 1), "$AAPL", author="b")] + _listposts(9, 10, "b"), R_BIG)
    assert ("AAPL", "2020-10-01") in {(x["ticker"], x["date"]) for x in t2}


def test_name_rule_and_serializable():
    cfg = ListFilterConfig()
    assert cfg.is_bot_name("AutoModerator") and cfg.is_bot_name("SomeTradingBot")
    assert cfg.is_bot_name("foo_automoderator") and not cfg.is_bot_name("botany_fan")
    assert ListFilterConfig.from_dict(json.loads(json.dumps(cfg.to_dict()))) == cfg
    agg = TickerDayAggregator(R)
    agg.add(item(0, utc(2020, 1, 1), "$TSLA", author="b"), bot_name=True)
    assert agg.finish() == ([], []) and agg.stats["bot_post"][("stocks", 2020)] == 1
