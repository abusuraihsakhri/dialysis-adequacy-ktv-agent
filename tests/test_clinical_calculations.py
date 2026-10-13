"""Clinical reference cases and safety-critical error conditions."""
import math
import pytest

from ktv_sentinel import calc_spktv, calc_stdktv, calc_nPCR, full_adequacy_assessment
from agents.base import AuditTrail


def test_reference_spktv_and_minimum_target_distinction():
    result = calc_spktv(60, 15, 4, 2.5, 75)
    expected = -math.log(0.25 - 0.032) + (4 - 3.5 * 0.25) * (2.5 / 75)
    assert result["spktv"] == round(expected, 3)
    assert result["minimum_spktv"] == 1.2
    assert result["target_spktv"] == 1.4


def test_fixed_volume_weekly_stdktv():
    sp = 1.4
    e = sp - 0.6 * sp / 4 + 0.03
    fraction = 1 - math.exp(-e)
    expected = 168 * fraction / 4 / (fraction / e + 168 / (3 * 4) - 1)
    result = calc_stdktv(sp, 3, 4)
    assert result["stdktv"] == round(expected, 3)
    assert result["minimum_stdktv"] == 2.1
    assert result["target_stdktv"] == 2.3


def test_npcr_depner_daugirdas_midweek():
    sp = calc_spktv(60, 15, 4, 2.5, 75)["spktv"]
    expected = 60 / (25.8 + 1.15 * sp + 56.4 / sp) + 0.168
    result = calc_nPCR(60, 15, 4, 2.5, 75)
    # Internal method uses unrounded Kt/V: allow its published rounding.
    assert result["npcr_g_kg_day"] == pytest.approx(expected, abs=0.001)
    assert result["generation_rate_mg_min"] is None
    assert calc_nPCR(60, 15, 4, 2.5, 75, session_position="beginning")["npcr_g_kg_day"] != result["npcr_g_kg_day"]


@pytest.mark.parametrize("pre,post,hours,uf,weight", [
    (60, 0.5, 24, 2, 70), (60, 15, 0, 2, 70),
    (60, 15, 4, -1, 70), (60, 15, 4, 2, float("nan")),
    (float("inf"), 15, 4, 2, 70), (60, 60, 4, 2, 70),
])
def test_invalid_spktv_rejected(pre, post, hours, uf, weight):
    with pytest.raises(ValueError):
        calc_spktv(pre, post, hours, uf, weight)


def test_fractional_frequency_rejected_and_npcr_not_extrapolated():
    with pytest.raises(ValueError):
        calc_stdktv(1.2, 3.5, 4)
    result = full_adequacy_assessment(60, 15, 4, 2.5, 75, 4)
    assert result["npcr"] is None


def test_hmac_detects_tampering_of_signed_fields_even_when_links_match():
    trail = AuditTrail(secret_key="unit-test")
    trail.log("actor", "tier", "EVENT", {"x": 1})
    assert trail.verify_integrity()
    detached = trail.get_trail()
    detached[0]["event_type"] = "FAKE"
    assert trail.verify_integrity()
    trail.logs[0]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()
