import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from dund import sealed as S  # noqa: E402
from dund.labels import PriceSeries  # noqa: E402


def ts(y, m, d):
    return datetime(y, m, d, tzinfo=timezone.utc)


def test_blocks_and_edges():
    assert S.is_sealed(date(2020, 6, 1))
    assert S.is_sealed(date(2020, 1, 1) - timedelta(days=S.PURGE_DAYS))
    assert not S.is_sealed(date(2020, 1, 1) - timedelta(days=S.PURGE_DAYS + 1))
    assert S.is_sealed(date(2020, 12, 31) + timedelta(days=S.EMBARGO_DAYS))
    assert not S.is_sealed(date(2020, 12, 31) + timedelta(days=S.EMBARGO_DAYS + 1))
    assert S.is_sealed(date(2023, 5, 5))
    assert not S.is_sealed(date(2019, 1, 1))


def test_forward_window_touch():
    d = date(2020, 1, 1) - timedelta(days=S.PURGE_DAYS + 15)
    assert not S.is_sealed_event(d, 1)
    assert S.is_sealed_event(d, 21)


def _series():
    ds = [date(2019, 1, 1) + timedelta(days=i) for i in range(40)]
    return PriceSeries("X", ds, [10.0] * 40, [10.0] * 40, [1e6] * 40)


def test_refused_without_token(tmp_path):
    log = str(tmp_path / "a.log")
    with pytest.raises(S.SealedAccessError):
        S.label_event_guarded("X", ts(2020, 5, 5), _series(), {})
    with pytest.raises(S.SealedAccessError):
        S.check_access(ts(2020, 5, 5), 10, unseal_token="nope", reason="r", audit_log=log)
    with pytest.raises(S.SealedAccessError):
        S.check_access(ts(2020, 5, 5), 10, unseal_token=S.UNSEAL_TOKEN, reason="", audit_log=log)
    assert not Path(log).exists()


def test_unseal_logs(tmp_path):
    log = str(tmp_path / "a.log")
    assert S.check_access(ts(2020, 5, 5), 10, unseal_token=S.UNSEAL_TOKEN, reason="why", audit_log=log)
    assert "UNSEAL" in Path(log).read_text()
    assert S.check_access(ts(2019, 1, 5), 10, audit_log=log) is False
    assert len(Path(log).read_text().splitlines()) == 1
