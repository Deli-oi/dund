"""Point-in-time label builder (docs/35-label-builder.md). Pure stdlib."""
from __future__ import annotations

import bisect
import csv
import gzip
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

CLOSE_UTC = time(21, 0)  # fixed 21:00 UTC close (16:00 ET in EST; see doc 35)
MAX_ENTRY_GAP_DAYS = 5
WINDOWS = (1, 5, 10, 21, 63)
PLACEBO_LOOKBACK = 252
MIN_PLACEBO = 100
PRICE_FLOOR = 1.0
ADV_FLOOR = 500_000.0
MCAP_FLOOR = 50_000_000.0
ADV_DAYS = 20
DELIST_DROP = -0.5  # final close this far below the previous is labelled 'delisted'


@dataclass
class PriceSeries:
    ticker: str
    dates: List[date]
    close: List[float]       # unadjusted, for price/liquidity floors
    adj_close: List[float]   # returns are computed on this
    volume: List[float]

    def __post_init__(self):
        n = len(self.dates)
        if not (len(self.close) == len(self.adj_close) == len(self.volume) == n):
            raise ValueError("column length mismatch")
        if any(self.dates[i] >= self.dates[i + 1] for i in range(n - 1)):
            raise ValueError("dates must be strictly increasing")

    def __len__(self):
        return len(self.dates)

    @property
    def last_date(self) -> Optional[date]:
        return self.dates[-1] if self.dates else None


def series_from_rows(ticker: str, rows: Iterable[dict]) -> PriceSeries:
    """Rows need date, close, adj_close (or adjclose), volume. Rows with blank/non-positive prices are
    dropped (missing); duplicate dates keep the last row."""
    by_date: Dict[date, Tuple[float, float, float]] = {}
    for r in rows:
        try:
            d = date.fromisoformat(str(r["date"])[:10])
            c = float(r["close"])
            a_raw = r.get("adj_close")
            if a_raw in (None, ""):
                a_raw = r.get("adjclose")
            if a_raw in (None, ""):
                continue  # no adjusted price: missing, never fall back to unadjusted close
            a = float(a_raw)
            v = float(r.get("volume") or 0.0)
        except (KeyError, ValueError, TypeError):
            continue
        if c != c or a != a or c <= 0 or a <= 0:
            continue
        by_date[d] = (c, a, v)
    ds = sorted(by_date)
    return PriceSeries(ticker, ds, [by_date[d][0] for d in ds],
                       [by_date[d][1] for d in ds], [by_date[d][2] for d in ds])


def load_prices(path: str, ticker: Optional[str] = None) -> PriceSeries:
    """Load one gzipped (or plain) CSV: date,open,high,low,close,adj_close,volume."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if ticker is None:
        ticker = os.path.basename(str(path)).split(".")[0].upper()
    return series_from_rows(ticker, rows)


def _as_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _nth_sunday(year: int, month: int, n: int) -> date:
    first = date(year, month, 1)
    first_sunday = 1 + (6 - first.weekday()) % 7
    return date(year, month, first_sunday + 7 * (n - 1))


def _is_half_day(d: date) -> bool:
    """NYSE early closes (13:00 ET): day after Thanksgiving, Dec 24 and Jul 3 when weekdays."""
    if d.weekday() >= 5:
        return False
    if (d.month, d.day) in ((12, 24), (7, 3)):
        return True
    thanksgiving = _nth_weekday(d.year, 11, 3, 4)  # 4th Thursday
    return d == thanksgiving + timedelta(days=1)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return date(year, month, 1 + (weekday - first.weekday()) % 7 + 7 * (n - 1))


def close_utc(d: date) -> time:
    """US equity close in UTC: 20:00 during US daylight time (2nd Sunday of March to
    1st Sunday of November, rules in force since 2007), else 21:00. Using 21:00 in summer
    would treat an already-printed close as still in the future (look-ahead)."""
    start, end = _nth_sunday(d.year, 3, 2), _nth_sunday(d.year, 11, 1)
    dst = start <= d < end
    if _is_half_day(d):  # 13:00 ET
        return time(17, 0) if dst else time(18, 0)
    return time(20, 0) if dst else time(21, 0)


def entry_index(series: PriceSeries, ts: datetime) -> Optional[int]:
    """Index of the first trading day whose close is STRICTLY after ts (close time is
    DST-aware, see close_utc). A trading day is a date present in the series.
    Weekends/holidays/after-close roll to the next present date. None if no such day."""
    t = _as_utc(ts)
    d = t.date()
    first_day = d if t.time() < close_utc(d) else date.fromordinal(d.toordinal() + 1)
    i = bisect.bisect_left(series.dates, first_day)
    if i >= len(series):
        return None
    # A series that starts long after the post (post-reorg or post-IPO history, or a reused
    # ticker symbol) is a different entity or a future price, not an entry. Longest real gap
    # is a long weekend plus a holiday, so allow a few calendar days only.
    if (series.dates[i] - first_day).days > MAX_ENTRY_GAP_DAYS:
        return None
    return i


@dataclass
class Window:
    n: int
    car: Optional[float] = None          # abnormal return, entry close -> close n days later
    raw_return: Optional[float] = None
    benchmark_return: Optional[float] = None
    placebo_percentile: Optional[float] = None  # share of placebo CARs <= car
    placebo_p95: Optional[float] = None
    n_placebo: int = 0
    reason: Optional[str] = None         # why car / percentile is None


@dataclass
class EventLabel:
    ticker: str
    ts: datetime
    entry_date: Optional[date] = None
    entry_price: Optional[float] = None
    windows: Dict[int, Window] = field(default_factory=dict)
    missing_price: bool = False
    illiquid: bool = False
    illiquid_reasons: List[str] = field(default_factory=list)
    market_cap_unknown: bool = False
    reason: Optional[str] = None         # event-level reason when nothing computable


def _ret(adj: Sequence[float], i: int, j: int) -> float:
    return adj[j] / adj[i] - 1.0


def _bench_return(bench: Dict[str, PriceSeries], d0: date, d1: date) -> Optional[float]:
    """Equal-weight mean of the supplied benchmark series' returns d0 -> d1.
    None if any benchmark lacks either date."""
    rs = []
    for s in bench.values():
        i = bisect.bisect_left(s.dates, d0)
        j = bisect.bisect_left(s.dates, d1)
        if i >= len(s) or j >= len(s) or s.dates[i] != d0 or s.dates[j] != d1:
            return None
        rs.append(_ret(s.adj_close, i, j))
    return sum(rs) / len(rs) if rs else None


def placebo_cars(series: PriceSeries, bench: Dict[str, PriceSeries], i0: int, n: int,
                 event_dates: Iterable[date] = (), lookback: int = PLACEBO_LOOKBACK
                 ) -> List[float]:
    """CARs of n-day windows of the same ticker with entry index j in [i0-lookback, i0-1]
    and exit index j+n <= i0-1 (every price used is a close at or before ts).
    Windows that start on or contain an event date are skipped."""
    ev = set(event_dates)
    out = []
    for j in range(max(0, i0 - lookback), i0 - n):
        k = j + n
        if ev and any(series.dates[m] in ev for m in range(j, k + 1)):
            continue
        b = _bench_return(bench, series.dates[j], series.dates[k])
        if b is None:
            continue
        out.append(_ret(series.adj_close, j, k) - b)
    return out


def _nearest_rank(sorted_vals: List[float], q: float) -> float:
    import math
    k = max(1, math.ceil(q * len(sorted_vals) - 1e-12))
    return sorted_vals[min(k, len(sorted_vals)) - 1]


def label_event(ticker: str, ts: datetime, series: Optional[PriceSeries],
                benchmarks: Dict[str, PriceSeries], *,
                windows: Sequence[int] = WINDOWS,
                event_dates: Iterable[date] = (),
                market_cap: Optional[float] = None,
                min_placebo: int = MIN_PLACEBO,
                lookback: int = PLACEBO_LOOKBACK,
                price_floor: float = PRICE_FLOOR, adv_floor: float = ADV_FLOOR,
                mcap_floor: float = MCAP_FLOOR) -> EventLabel:
    """benchmarks: {"market": spy} or {"market": spy, "sector": xlk}.
    event_dates: this ticker's event dates (excluded from placebo windows)."""
    lab = EventLabel(ticker=ticker, ts=ts)
    if series is None or len(series) == 0:
        lab.missing_price, lab.reason = True, "missing_price:no_series"
        return lab
    mkt_end = min((s.last_date for s in benchmarks.values() if s.last_date), default=None)
    ended_early = mkt_end is not None and series.last_date < mkt_end
    end_reason = "series_ended_early"
    if ended_early and len(series) >= 2 and series.close[-1] / series.close[-2] - 1.0 <= DELIST_DROP:
        end_reason = "delisted"
    i0 = entry_index(series, ts)
    if i0 is None:
        lab.missing_price = True
        lab.reason = end_reason if ended_early else "missing_price:no_entry_after_ts"
        return lab
    lab.entry_date, lab.entry_price = series.dates[i0], series.close[i0]

    # liquidity, point-in-time: ADV uses only days strictly before the entry day
    if lab.entry_price < price_floor:
        lab.illiquid_reasons.append("price")
    lo = max(0, i0 - ADV_DAYS)
    if i0 - lo < ADV_DAYS:
        lab.illiquid_reasons.append("adv_insufficient_history")
    else:
        adv = sum(series.close[m] * series.volume[m] for m in range(lo, i0)) / ADV_DAYS
        if adv < adv_floor:
            lab.illiquid_reasons.append("adv")
    if market_cap is None:
        lab.market_cap_unknown = True
    elif market_cap < mcap_floor:
        lab.illiquid_reasons.append("market_cap")
    lab.illiquid = bool(lab.illiquid_reasons)

    for n in windows:
        w = Window(n=n)
        lab.windows[n] = w
        j = i0 + n
        if j >= len(series):
            w.reason = end_reason if ended_early else "insufficient_forward_window"
            continue
        b = _bench_return(benchmarks, series.dates[i0], series.dates[j])
        if b is None:
            w.reason = "missing_benchmark"
            continue
        w.raw_return = _ret(series.adj_close, i0, j)
        w.benchmark_return = b
        w.car = w.raw_return - b
        past = [e for e in event_dates if e < series.dates[i0]]  # never future events
        pl = sorted(placebo_cars(series, benchmarks, i0, n, past, lookback))
        w.n_placebo = len(pl)
        if len(pl) < min_placebo:
            w.reason = "insufficient_placebo"
            continue
        w.placebo_percentile = sum(1 for x in pl if x <= w.car) / len(pl)
        w.placebo_p95 = _nearest_rank(pl, 0.95)
    return lab


def hit_label(lab: EventLabel, *, window: int = 10, car_floor: float = 0.03,
              placebo_q: float = 0.95, require_liquid: bool = True
              ) -> Tuple[Optional[bool], Optional[str]]:
    """Returns (label, reason). label is True/False, or None (never False) when the
    outcome is unknowable: missing price, ended/insufficient window, missing benchmark,
    too few placebo windows, or illiquid (if require_liquid).
    Hit = car >= car_floor AND placebo_percentile > placebo_q (strict)."""
    if lab.missing_price:
        return None, lab.reason or "missing_price"
    w = lab.windows.get(window)
    if w is None:
        return None, "window_not_computed"
    if w.car is None:
        return None, w.reason
    if require_liquid and lab.illiquid:
        return None, "illiquid:" + ",".join(lab.illiquid_reasons)
    if w.placebo_percentile is None:
        return None, w.reason or "insufficient_placebo"
    return (w.car >= car_floor and w.placebo_percentile > placebo_q), None
