import csv
import gzip
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import build_exploratory as B  # noqa: E402


def write_prices(p, n=400, start=date(2018, 1, 1), g=0.001):
    with gzip.open(p, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "adjclose", "volume"])
        for i in range(n):
            d = start + timedelta(days=i)
            px = 100 * (1 + g) ** i
            w.writerow([d.isoformat(), px, px, px, px, px, 1e7])


def test_build(tmp_path):
    pr = tmp_path / "p"
    pr.mkdir()
    write_prices(pr / "SPY.csv.gz")
    write_prices(pr / "AAA.csv.gz", g=0.002)
    td = tmp_path / "td.csv.gz"
    days = [date(2018, 12, 1), date(2018, 12, 15), date(2020, 6, 1), date(2018, 12, 20)]
    with gzip.open(td, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "date", "decision_ts", "subs_json"])
        for d in days:
            w.writerow(["AAA", d.isoformat(),
                        (d + timedelta(days=1)).isoformat() + "T00:00:00+00:00", '{"wsb": 1}'])
        w.writerow(["ZZZ", "2018-12-10", "2018-12-11T00:00:00+00:00", '{"wsb": 1}'])
    out = tmp_path / "o"
    n, ns = B.build(str(td), str(pr), str(out))
    assert ns == 1 and n == 4
    rows = list(csv.DictReader(gzip.open(out / "exploratory_events.csv.gz", "rt")))
    assert all(r["date"] != "2020-06-01" for r in rows)
    zzz = [r for r in rows if r["ticker"] == "ZZZ"][0]
    assert zzz["hit10"] == "" and zzz["reason"]
    cov = (out / "coverage.md").read_text()
    assert "sealed ticker-days skipped (prices never read): 1" in cov
    assert "None is never a miss" in cov
    # table sums: None share + observable share == 100% in the total
    assert "observable (hit is True/False): " in cov


def test_none_not_miss():
    assert B.classify(None) is None
    assert B.classify("missing_price:no_series") == "no_series"
    assert B.classify("illiquid:adv") == "illiquid"
