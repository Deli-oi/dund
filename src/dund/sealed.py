"""Sealed-period configuration and guards (docs/32 section 12, docs/38 D5). Pure stdlib."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

UNSEAL_TOKEN = "I-ACCEPT-ONE-TIME-UNSEAL"
# 20 trading days is at most 28 calendar days; use 30 to be conservative.
PURGE_DAYS = 30
EMBARGO_DAYS = 30
# forward windows: trading days -> calendar days (x7/5, plus holiday and entry-gap slack)
ENTRY_SLACK_DAYS = 7

BLOCKS = {
    "A": (date(2020, 1, 1), date(2020, 12, 31)),
    "B": (date(2021, 7, 1), date(2022, 6, 30)),
    "EXT": (date(2023, 1, 1), date(2023, 12, 31)),
}


class SealedAccessError(RuntimeError):
    pass


def _d(x) -> date:
    if isinstance(x, datetime):
        if x.tzinfo is not None:
            x = x.astimezone(timezone.utc)
        return x.date()
    if isinstance(x, date):
        return x
    s = str(x)
    if len(s) > 10:
        return _d(datetime.fromisoformat(s.replace("Z", "+00:00")))
    return date.fromisoformat(s[:10])


def block_zone(name: str):
    s, e = BLOCKS[name]
    return s - timedelta(days=PURGE_DAYS), e + timedelta(days=EMBARGO_DAYS)


def is_sealed(d) -> bool:
    """True if date d is inside a block or its purge/embargo zone."""
    d = _d(d)
    return any(block_zone(n)[0] <= d <= block_zone(n)[1] for n in BLOCKS)


def window_calendar_days(window_days: int) -> int:
    return -(-window_days * 7 // 5) + ENTRY_SLACK_DAYS


def is_sealed_event(decision_ts, window_days: int) -> bool:
    """True if the decision day, any day of the forward label window (conservative calendar
    span), or the purge zone touches a sealed block."""
    d0 = _d(decision_ts)
    d1 = d0 + timedelta(days=window_calendar_days(window_days))
    return any(not (d1 < block_zone(n)[0] or d0 > block_zone(n)[1]) for n in BLOCKS)


def check_access(decision_ts, window_days: int, *, unseal_token: Optional[str] = None,
                 reason: Optional[str] = None, audit_log: Optional[str] = None,
                 who: str = "") -> bool:
    """False if the event is not sealed. True if sealed AND validly unsealed (line appended to
    audit_log). Raises SealedAccessError otherwise."""
    if not is_sealed_event(decision_ts, window_days):
        return False
    if (unseal_token != UNSEAL_TOKEN or not reason or not str(reason).strip()
            or not audit_log):
        raise SealedAccessError("sealed event %s (window %s): refused" % (decision_ts, window_days))
    line = "%s\tUNSEAL\t%s\twindow=%s\t%s\t%s\n" % (
        datetime.now(timezone.utc).isoformat(), _d(decision_ts), window_days, who,
        " ".join(str(reason).split()))
    with open(audit_log, "a", encoding="utf-8") as fh:
        fh.write(line)
    return True


def label_event_guarded(ticker, ts, series, benchmarks, *, window_days=21,
                        unseal_token=None, reason=None, audit_log=None, **kw):
    """labels.label_event behind the seal. Raises for sealed events without unseal."""
    from dund.labels import label_event
    check_access(ts, window_days, unseal_token=unseal_token, reason=reason,
                 audit_log=audit_log, who=ticker)
    return label_event(ticker, ts, series, benchmarks, **kw)
