import gzip
import os
import random
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

from dund.labels import PriceSeries, entry_index, hit_label, label_event, load_prices

UTC = timezone.utc


def bdays(start, n, skip=()):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5 and d not in skip:
            out.append(d)
        d += timedelta(days=1)
    return out


def mk(ticker, dates, px, vol=1e6):
    return PriceSeries(ticker, list(dates), list(px), list(px), [vol] * len(dates))


def walk(n, seed, vol=0.01, p0=50.0):
    r = random.Random(seed)
    p, out = p0, []
    for _ in range(n):
        p *= 1 + r.gauss(0, vol)
        out.append(p)
    return out


HOL = {date(2023, 1, 16)}  # holiday absent from series
DATES = bdays(date(2023, 1, 2), 420, skip=HOL)


def world(px=None, seed=1):
    mkt = mk("SPY", DATES, [100.0] * len(DATES))  # flat market -> CAR == raw return
    return mk("X", DATES, px if px is not None else walk(len(DATES), seed)), {"market": mkt}


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.s, _ = world()

    def d(self, ts):
        return self.s.dates[entry_index(self.s, ts)]

    def test_intraday_same_day_close(self):
        self.assertEqual(self.d(datetime(2023, 3, 1, 15, 0, tzinfo=UTC)), date(2023, 3, 1))

    def test_after_close_next_day(self):
        self.assertEqual(self.d(datetime(2023, 3, 1, 21, 0, tzinfo=UTC)), date(2023, 3, 2))
        self.assertEqual(self.d(datetime(2023, 3, 1, 23, 30, tzinfo=UTC)), date(2023, 3, 2))

    def test_weekend(self):
        self.assertEqual(self.d(datetime(2023, 3, 4, 12, 0, tzinfo=UTC)), date(2023, 3, 6))
        self.assertEqual(self.d(datetime(2023, 3, 5, 23, 0, tzinfo=UTC)), date(2023, 3, 6))

    def test_friday_after_close(self):
        self.assertEqual(self.d(datetime(2023, 3, 3, 22, 0, tzinfo=UTC)), date(2023, 3, 6))

    def test_holiday(self):
        self.assertEqual(self.d(datetime(2023, 1, 16, 14, 0, tzinfo=UTC)), date(2023, 1, 17))
        self.assertEqual(self.d(datetime(2023, 1, 13, 22, 0, tzinfo=UTC)), date(2023, 1, 17))

    def test_naive_is_utc_and_tz_converted(self):
        self.assertEqual(self.d(datetime(2023, 3, 1, 22, 0)), date(2023, 3, 2))
        est = timezone(timedelta(hours=-5))
        self.assertEqual(self.d(datetime(2023, 3, 1, 17, 0, tzinfo=est)), date(2023, 3, 2))

    def test_after_series_end_none(self):
        self.assertIsNone(entry_index(self.s, datetime(2030, 1, 1, tzinfo=UTC)))


class LabelTests(unittest.TestCase):
    TS = datetime(2023, 11, 1, 15, 0, tzinfo=UTC)

    def lab(self, px, ts=None, **kw):
        s, b = world(px)
        return label_event("X", ts or self.TS, s, b, **kw)

    def i0(self):
        s, _ = world()
        return entry_index(s, self.TS)

    def test_car_and_hit(self):
        px, i0 = walk(len(DATES), 3), self.i0()
        px[i0 + 10] = px[i0] * 1.40
        lab = self.lab(px)
        self.assertAlmostEqual(lab.windows[10].car, 0.40, places=9)
        self.assertEqual(lab.entry_date, DATES[i0])
        self.assertEqual(hit_label(lab), (True, None))

    def test_small_move_false_not_none(self):
        px, i0 = walk(len(DATES), 3), self.i0()
        px[i0 + 10] = px[i0] * 1.01
        self.assertEqual(hit_label(self.lab(px)), (False, None))

    def test_param_rule(self):
        px, i0 = walk(len(DATES), 3), self.i0()
        px[i0 + 5] = px[i0] * 1.40
        lab = self.lab(px)
        self.assertEqual(hit_label(lab, window=5, car_floor=0.10)[0], True)
        self.assertEqual(hit_label(lab, window=5, car_floor=0.90)[0], False)

    def test_no_lookahead_after_window(self):
        px, i0 = walk(len(DATES), 5), self.i0()
        px[i0 + 10] = px[i0] * 1.2
        a = self.lab(list(px))
        px2 = list(px)
        for k in range(i0 + 11, len(px2)):
            px2[k] *= 7.0
        b = self.lab(px2)
        self.assertEqual(a.windows[10], b.windows[10])
        self.assertEqual(hit_label(a), hit_label(b))

    def test_before_T_only_through_placebo(self):
        px, i0 = walk(len(DATES), 5), self.i0()
        a = self.lab(list(px))
        px2 = list(px)
        for k in range(0, i0):
            px2[k] *= 1.0 + 0.05 * ((k % 7) - 3)
        b = self.lab(px2)
        wa, wb = a.windows[10], b.windows[10]
        self.assertEqual((wa.car, wa.raw_return, a.entry_price),
                         (wb.car, wb.raw_return, b.entry_price))
        self.assertNotEqual(wa.placebo_p95, wb.placebo_p95)

    def test_placebo_ignores_entry_day_and_future(self):
        px, i0 = walk(len(DATES), 7), self.i0()
        a = self.lab(list(px))
        px2 = list(px)
        px2[i0] *= 1.5
        px2[i0 + 10] = px[i0 + 10] * 1.5  # same 10d return
        b = self.lab(px2)
        self.assertEqual(a.windows[10].placebo_p95, b.windows[10].placebo_p95)

    def test_event_dates_excluded_from_placebo(self):
        px, i0 = walk(len(DATES), 9), self.i0()
        a = self.lab(px)
        b = self.lab(px, event_dates=[DATES[i0 - 50]])
        self.assertLess(b.windows[10].n_placebo, a.windows[10].n_placebo)

    def test_missing_series_none(self):
        _, b = world()
        lab = label_event("X", self.TS, None, b)
        r = hit_label(lab)
        self.assertIsNone(r[0])
        self.assertIn("missing_price", r[1])

    def test_missing_benchmark_none(self):
        s, _ = world()
        mkt = mk("SPY", DATES[:200], [100.0] * 200)
        lab = label_event("X", self.TS, s, {"market": mkt})
        self.assertIsNone(hit_label(lab)[0])

    def test_delisted_none_with_reason(self):
        s, b = world()
        cut = DATES.index(date(2023, 11, 3))
        s2 = mk("X", DATES[:cut + 1], s.close[:cut + 1])
        lab = label_event("X", self.TS, s2, b)
        self.assertEqual(hit_label(lab), (None, "delisted_or_series_ended"))
        self.assertIsNone(lab.windows[10].car)
        self.assertIsNotNone(lab.windows[1].car)

    def test_insufficient_forward_window_all_data_ends(self):
        s, _ = world()
        n = DATES.index(date(2023, 11, 3)) + 1
        s2 = mk("X", DATES[:n], s.close[:n])
        b2 = {"market": mk("SPY", DATES[:n], [100.0] * n)}
        lab = label_event("X", self.TS, s2, b2)
        self.assertEqual(hit_label(lab), (None, "insufficient_forward_window"))

    def test_post_after_series_end(self):
        s, b = world()
        lab = label_event("X", self.TS, mk("X", DATES[:100], s.close[:100]), b)
        self.assertEqual(hit_label(lab), (None, "delisted_or_series_ended"))
        self.assertTrue(lab.missing_price)

    def test_insufficient_placebo(self):
        s, b = world(walk(len(DATES), 3))
        ts = datetime.combine(DATES[60], datetime.min.time(), tzinfo=UTC)
        lab = label_event("X", ts, s, b)
        self.assertEqual(hit_label(lab), (None, "insufficient_placebo"))

    def test_illiquid_floors(self):
        lab = self.lab([0.5] * len(DATES))
        self.assertIn("price", lab.illiquid_reasons)
        self.assertIsNone(hit_label(lab)[0])
        s, b = world()
        thin = PriceSeries("X", s.dates, s.close, s.adj_close, [10.0] * len(s))
        self.assertIn("adv", label_event("X", self.TS, thin, b).illiquid_reasons)
        self.assertIn("market_cap", label_event("X", self.TS, s, b, market_cap=1e6).illiquid_reasons)
        l4 = label_event("X", self.TS, s, b)
        self.assertTrue(l4.market_cap_unknown)
        self.assertFalse(l4.illiquid)

    def test_sector_benchmark(self):
        s, b = world()
        sec = mk("XLK", DATES, [100.0 * 1.001 ** i for i in range(len(DATES))])
        lab = label_event("X", self.TS, s, {"market": b["market"], "sector": sec})
        self.assertAlmostEqual(lab.windows[10].benchmark_return, (1.001 ** 10 - 1) / 2, places=9)

    def test_loader(self):
        p = os.path.join(tempfile.mkdtemp(), "abc.csv.gz")
        with gzip.open(p, "wt") as f:
            f.write("date,open,high,low,close,adj_close,volume\n"
                    "2023-01-03,1,1,1,10,9,100\n2023-01-04,1,1,1,,,\n2023-01-05,1,1,1,11,10,50\n")
        s = load_prices(p)
        self.assertEqual((s.ticker, len(s)), ("ABC", 2))


if __name__ == "__main__":
    unittest.main()


class DstCloseTest(unittest.TestCase):
    def _series(self):
        ds = [date(2021, 7, 12) + timedelta(days=i) for i in range(10) if (date(2021, 7, 12) + timedelta(days=i)).weekday() < 5]
        return mk("X", ds, [10.0 + i for i in range(len(ds))])

    def test_summer_post_after_2000utc_enters_next_day(self):
        s = self._series()
        # 2021-07-13 20:30 UTC is 16:30 EDT, after the close at 20:00 UTC
        i = entry_index(s, datetime(2021, 7, 13, 20, 30, tzinfo=timezone.utc))
        self.assertEqual(s.dates[i], date(2021, 7, 14))

    def test_summer_post_before_close_enters_same_day(self):
        s = self._series()
        i = entry_index(s, datetime(2021, 7, 13, 19, 30, tzinfo=timezone.utc))
        self.assertEqual(s.dates[i], date(2021, 7, 13))

    def test_winter_close_is_2100utc(self):
        ds = [date(2021, 1, 4) + timedelta(days=i) for i in range(5)]
        s = mk("X", ds, [10.0] * 5)
        i = entry_index(s, datetime(2021, 1, 5, 20, 30, tzinfo=timezone.utc))
        self.assertEqual(s.dates[i], date(2021, 1, 5))
