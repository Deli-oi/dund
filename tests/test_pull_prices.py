import gzip
import importlib.util
from pathlib import Path

import pytest

_p = Path(__file__).resolve().parents[1] / "scripts" / "pull_prices.py"
_s = importlib.util.spec_from_file_location("pull_prices", _p)
pp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pp)

CANNED = {"chart": {"result": [{
    "timestamp": [1325601000, 1325687400, 1325773800],
    "indicators": {
        "quote": [{"open": [1, 2, None], "high": [2, 3, None], "low": [1, 2, None],
                   "close": [1.5, 2.5, None], "volume": [100, 200, None]}],
        "adjclose": [{"adjclose": [1.4, 2.4, None]}]},
    "events": {"dividends": {"1325687400": {"amount": 0.1}},
               "splits": {"1325601000": {"numerator": 2, "denominator": 1}}},
}], "error": None}}


def test_normalize():
    assert pp.normalize_ticker(" brk.b ") == "BRK-B"
    assert pp.normalize_ticker("^gspc") == "^GSPC"
    assert pp.normalize_ticker("BF-B") == "BF-B"


def test_parse_chart():
    rows = pp.parse_chart(CANNED)
    assert len(rows) == 2  # null-close day dropped
    assert rows[0]["adjclose"] == 1.4 and rows[0]["split"] == "2:1"
    assert rows[1]["dividend"] == 0.1


def test_parse_error():
    with pytest.raises(ValueError):
        pp.parse_chart({"chart": {"result": None, "error": {"description": "Not Found"}}})


def test_resume(tmp_path):
    (tmp_path / "manifest.tsv").write_text("ticker\tfirst_date\tlast_date\trows\nAAPL\ta\tb\t1\n")
    (tmp_path / "misses.tsv").write_text("ticker\thttp_status\treason\nBBBY\t404\tx\n")
    assert pp.load_done(tmp_path) == {"AAPL", "BBBY"}


def test_atomic_write(tmp_path):
    f = tmp_path / "X.csv.gz"
    pp.write_rows_atomic(f, pp.parse_chart(CANNED))
    assert f.exists() and not list(tmp_path.glob("*.tmp"))
    assert gzip.open(f, "rt").read().startswith("date,open")
