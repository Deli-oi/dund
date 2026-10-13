import json
import math

import pytest

from dund.confidence import (confidence, decisiveness, effective_n, evidence_quality,
                             example_weight, reasons)
from dund.ledger import CapExceeded, Killed, Ledger
from dund.report import Call, breakeven_threshold, rank


def test_decisiveness_bounds():
    assert decisiveness(0.5) == 0.0
    assert decisiveness(1.0) == 1.0
    assert decisiveness(0.0) == 1.0
    with pytest.raises(ValueError):
        decisiveness(1.2)


def test_confidence_multiplies_factors():
    f = {"entity_resolution": 0.5, "outcome_measurement": 0.8}
    assert evidence_quality(f) == pytest.approx(0.4)
    assert confidence(0.9, f) == pytest.approx(0.8 * 0.4)
    assert reasons(f) == ["entity_resolution"]


def test_worked_example_weight_matches_report():
    # docs report part 2: label 0.9 confidence, 2 years old, half-life 3
    w = example_weight(0.9, 2, 3)
    assert w == pytest.approx(0.9 * 0.63, abs=0.01)


def test_effective_n():
    assert effective_n([1, 1, 1, 1]) == pytest.approx(4)
    assert effective_n([10, 0.1, 0.1]) < 1.1


def test_cluster_share_downweights():
    assert example_weight(1, 0, 3, cluster_k=4) == pytest.approx(0.5)


def test_threshold_default_is_070():
    assert breakeven_threshold(1.0, 1.0) == pytest.approx(0.70)


def test_rank_by_margin_not_p():
    wide = Call("A", "1", p=0.90, p_lower=0.60, p_upper=0.97, threshold=0.70)
    tight = Call("B", "2", p=0.80, p_lower=0.75, p_upper=0.84, threshold=0.70)
    assert rank([wide, tight])[0].asset == "B"
    assert tight.action == "ACT"
    assert wide.action == "WATCH"


def test_confounded_never_acts():
    c = Call("A", "1", 0.95, 0.9, 0.99, 0.70, confounded=True)
    assert c.action == "SKIP"


def test_ledger_cap_and_kill(tmp_path):
    led = Ledger(tmp_path / "ledger.jsonl", {"usd": 10})
    led.record("usd", 6, "a")
    with pytest.raises(CapExceeded):
        led.record("usd", 5, "b")
    (tmp_path / "KILL").write_text("stop")
    with pytest.raises(Killed):
        led.record("usd", 1)
    assert led.totals()["usd"] == 6
    rows = [json.loads(l) for l in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and not math.isnan(rows[0]["ts"])
