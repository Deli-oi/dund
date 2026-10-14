# 31 - Synthetic power results (v2)

Status: Current (v2, October 14, 2026). Implements D8 of `38`. Part 1 is the power simulation for the real estimand; Part 2 is the old detection check, kept unchanged.

# Part 1 - Power for the real estimand (v2)

Code: `generate_v2` and `boot_lower_bounds` in `src/dund/synth.py`; driver `scripts/power_sim_v2.py`; tests `tests/test_synth_v2.py`. Pure stdlib.

## What is simulated

- Estimand (D1): for flagged ticker-days, 10-day net abnormal return minus the mean of 3 matched controls (same ticker, non-flagged, other week). Edge is planted as a NET effect; gross edge = net + 20 bps round-trip cost.
- Test (D4): one-sided, 95% lower bound of the mean difference above zero, from a multiplier bootstrap (99 draws) with Exp(1) cluster weights. Three variants on the same data: ticker-only (negative control, not accepted by D4), week-only, and two-way (product of ticker and calendar-week weights).
- Generator: ticker random effect (sd 2%); calendar-week common shock affecting all tickers (sd 3%, doubled in meme weeks); idiosyncratic noise from ticker-week innovations, with each 10-day window spanning three calendar weeks so windows overlap; high-attention days get an extra fat shock (35% of flagged days, 15% of controls); total 10-day sd about 9 to 10%. Flags are Zipf-concentrated in a few tickers, and 60% of flags fall in meme weeks (6% of weeks). Optional regime break: the edge exists only in the first half of the calendar.
- Scale: N ticker-days = flagged units / flag rate, spread at 400 ticker-days a week (about 20,000 a year, inside the docs/28 range of 8,000 to 34,000).

## (a) False-positive rate at edge 0 (2,000 null sims per row; Wilson 95% interval)

| flag rate | flagged | N | ticker-only | week-only | two-way |
|---|---|---|---|---|---|
| 0.5% | 100 | 20,000 | 0.136 [0.121, 0.151] | 0.076 [0.065, 0.088] | 0.025 [0.019, 0.033] |
| 0.5% | 400 | 80,000 | 0.143 [0.128, 0.159] | 0.043 [0.035, 0.052] | 0.017 [0.012, 0.024] |
| 0.1% | 100 | 100,000 | 0.065 [0.055, 0.076] | 0.045 [0.037, 0.056] | 0.005 [0.003, 0.009] |
| 0.1% | 400 | 400,000 | 0.068 [0.057, 0.079] | 0.043 [0.035, 0.052] | 0.005 [0.003, 0.009] |
| 2.0% | 100 | 5,000 | 0.153 [0.138, 0.169] | 0.078 [0.067, 0.091] | 0.029 [0.023, 0.037] |
| 2.0% | 400 | 20,000 | 0.263 [0.244, 0.282] | 0.096 [0.084, 0.110] | 0.050 [0.041, 0.060] |

Nominal is 0.05. Ticker-only clustering is anti-conservative under the week shock (0.14 to 0.26 at base case and 2%), confirming why D4 rejects it. The two-way test never exceeds nominal (0.005 to 0.050) and is conservative, so its power numbers below are somewhat pessimistic. Week-only is mildly inflated with few flagged weeks.

## (b, c) Units needed for 80% power, two-way test (200 sims per grid point, log-interpolated)

| flag rate | net edge (bps) | flagged units | ticker-days N | years at 20k a year |
|---|---|---|---|---|
| 0.5% (base) | 50 | about 10,500 | about 2.1M | about 105 |
| 0.5% | 100 | about 2,600 | about 515k | about 26 |
| 0.5% | 200 | about 640 | about 128k | about 6.4 |
| 0.5% | 300 | about 280 | about 55k | about 2.8 |
| 0.1% | 50 | about 6,400 | about 6.4M | about 320 |
| 0.1% | 100 | about 1,550 | about 1.5M | about 77 |
| 0.1% | 200 | about 485 | about 485k | about 24 |
| 0.1% | 300 | about 165 | about 164k | about 8.2 |
| 2.0% | 50 | more than 25,600 | more than 1.3M | n/a |
| 2.0% | 100 | about 6,500 | about 326k | about 16 |
| 2.0% | 200 | about 1,500 | about 77k | about 3.8 |
| 2.0% | 300 | about 480 | about 24k | about 1.2 |
| 0.5%, regime break | 100 / 200 / 300 | about 10,500 / 2,700 / 1,300 | 2.1M / 530k / 260k | 105 / 27 / 13 |

Edge 0 has no power by definition (see (a)). Week-only and ticker-only flagged counts are in the script output; ticker-only needs fewer only because it is inflated. Flagged units are not monotone in flag rate at fixed edge because a lower rate means more calendar weeks and so more meme weeks, hence more independent clusters; the 0.1% rows should be read as a sensitivity on the generator, not a free lunch.

## (d) Reading

The true net edge of a Reddit-mention flag is unknown, and nothing here estimates it. Plausible values include zero, and a net edge above 100 bps over 10 days after 20 bps cost would be a large effect for public, widely read signals; this is a prior, not a finding. Against the supply in `28` (about 8,000 to 34,000 independent ticker-days a year, so roughly 40 to 170 flags a year at 0.5%), the test can only detect edges of about 300 bps or more within several years (about 280 flags needs roughly 3 years at the high end of supply and about 7 at the low end). An edge of 100 bps needs about 2,600 flags, decades of data at this flag rate; 50 bps is out of reach. Practical implication: either the flag rate must be raised toward 2% (which loosens the flag and may dilute the edge, not modelled here), the history extended over the full 2012 to 2025 span, or the claim restricted to large effects. A null result will mostly mean "not detectable at this supply", not "no edge". The regime-break option roughly doubles the units needed for the same average edge (100 bps: about 10,500 vs 2,600 flags).

Caveats: noise, week-shock and meme-concentration parameters are assumptions; matched controls are idealised; the bootstrap is a multiplier bootstrap with few effective week clusters, which is conservative here. Runtime of the full default run is about 22 minutes on 12 cores; `python scripts/power_sim_v2.py 2000 60` (fewer power sims per grid point) is the quicker variant.

# Part 2 - Detection check: flagged vs base rate (old simulation)

Labelled as the detection check, not the registered test. Generated by `scripts/power_sim.py` (500 simulations per cell, 199 permutations each, alpha 0.05, one-sided). Data from `generate`: base rate 5%, flag rate 2%, about 4 ticker-days per ticker, log-normal ticker multiplier (sd 0.5). Test: flagged hit rate vs unflagged, flags permuted within ticker.

| scenario | N=2000 | N=5000 | N=10000 | N=20000 | N=40000 |
|---|---|---|---|---|---|
| null 5%->5% (false positives) | 0.024 | 0.036 | 0.030 | 0.040 | 0.028 |
| 5%->7% | 0.056 | 0.140 | 0.222 | 0.368 | 0.612 |
| 5%->10% | 0.180 | 0.426 | 0.708 | 0.968 | 0.994 |
| 5%->15% | 0.462 | 0.870 | 0.992 | 1.000 | 1.000 |

N for 80% power: 5%->15% about 4,500; 5%->10% about 13,500; 5%->7% more than 40,000. This simulation has no week shock, no net-return outcome and no cost, which is why Part 1 replaces it for planning.
