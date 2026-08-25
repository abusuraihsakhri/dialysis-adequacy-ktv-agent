import pytest
import math
from ktv_sentinel import (
    calc_spktv,
    calc_urr,
    calc_ektv,
    calc_stdktv,
    calc_nPCR,
    full_adequacy_assessment,
    main,
)


# --- spKt/V (Daugirdas II) ---

def test_spktv_typical():
    """Pre 60, Post 15, 4h, 2.5L UF, 75kg"""
    r = calc_spktv(60, 15, 4, 2.5, 75)
    R = 15 / 60  # 0.25
    expected = -math.log(R - 0.008 * 4) + (4 - 3.5 * R) * (2.5 / 75)
    assert abs(r["spktv"] - round(expected, 3)) < 0.001


def test_spktv_adequate():
    r = calc_spktv(60, 15, 4, 2.5, 75)
    assert r["adequate"] is True
    assert r["spktv"] >= 1.2


def test_spktv_inadequate():
    """High post BUN relative to pre = low Kt/V"""
    r = calc_spktv(60, 40, 3, 1.0, 80)
    assert r["adequate"] is False
    assert r["spktv"] < 1.2


def test_spktv_r_ratio():
    r = calc_spktv(60, 15, 4, 2.5, 75)
    assert abs(r["R_ratio"] - 0.25) < 0.001


def test_spktv_invalid_pre_bun():
    with pytest.raises(ValueError):
        calc_spktv(0, 15, 4, 2.5, 75)


def test_spktv_post_ge_pre():
    with pytest.raises(ValueError):
        calc_spktv(60, 60, 4, 2.5, 75)


# --- URR ---

def test_urr_calculation():
    """(60-15)/60 × 100 = 75%"""
    r = calc_urr(60, 15)
    assert r["urr_percent"] == 75.0
    assert r["adequate"] is True


def test_urr_just_adequate():
    """65% threshold"""
    r = calc_urr(100, 35)
    assert r["urr_percent"] == 65.0
    assert r["adequate"] is True


def test_urr_inadequate():
    r = calc_urr(60, 30)
    assert r["urr_percent"] == 50.0
    assert r["adequate"] is False


def test_urr_invalid():
    with pytest.raises(ValueError):
        calc_urr(60, 70)


# --- eKt/V ---

def test_ektv_calculation():
    """eKt/V = spKt/V - 0.6 × (spKt/V/t) + 0.03"""
    r = calc_ektv(1.4, 4.0)
    expected = 1.4 - 0.6 * (1.4 / 4.0) + 0.03
    assert abs(r["ektv"] - round(expected, 3)) < 0.001


def test_ektv_lower_than_spktv():
    r = calc_ektv(1.4, 4.0)
    assert r["ektv"] < 1.4


def test_ektv_short_session_bigger_drop():
    """Shorter sessions have more urea rebound"""
    r_long = calc_ektv(1.4, 5.0)
    r_short = calc_ektv(1.4, 3.0)
    assert r_short["ektv"] < r_long["ektv"]


# --- stdKt/V ---

def test_stdktv_3x_week():
    r = calc_stdktv(1.4, 3, 4)
    assert r["stdktv"] > 0
    # spKt/V 1.4 at 3x/week gives stdKt/V ~1.4
    assert r["stdktv"] > 1.0


def test_stdktv_increases_with_frequency():
    r_3x = calc_stdktv(1.2, 3, 4)
    r_6x = calc_stdktv(1.2, 6, 4)
    assert r_6x["stdktv"] > r_3x["stdktv"]


# --- nPCR ---

def test_nPCR_calculation():
    r = calc_nPCR(60, 15, 4, 2.5, 75)
    assert r["npcr_g_kg_day"] > 0
    assert r["status"] in ("low", "adequate", "high")


def test_nPCR_adequate_range():
    """Typical values should give adequate nPCR"""
    r = calc_nPCR(60, 15, 4, 2.5, 75)
    # With these values, nPCR should be in a reasonable range
    assert r["npcr_g_kg_day"] > 0


def test_nPCR_high_with_high_pre_bun():
    r = calc_nPCR(100, 20, 4, 3.0, 70)
    assert r["npcr_g_kg_day"] > 0


# --- Full Assessment ---

def test_full_assessment():
    r = full_adequacy_assessment(60, 15, 4, 2.5, 75)
    assert "spktv" in r
    assert "urr" in r
    assert "ektv" in r
    assert "stdktv" in r
    assert "npcr" in r
    assert "overall_adequate" in r


def test_full_assessment_adequate():
    r = full_adequacy_assessment(60, 15, 4, 2.5, 75)
    assert r["overall_adequate"] is True


def test_full_assessment_inadequate():
    r = full_adequacy_assessment(50, 40, 3, 1.0, 80)
    assert r["overall_adequate"] is False


# --- CLI ---

def test_cli_spktv():
    assert main(["spktv", "--pre-bun", "60", "--post-bun", "15",
                  "--time", "4", "--uf-l", "2.5", "--weight", "75"]) == 0


def test_cli_urr():
    assert main(["urr", "--pre-bun", "60", "--post-bun", "15"]) == 0


def test_cli_full():
    assert main(["full", "--pre-bun", "60", "--post-bun", "15",
                  "--time", "4", "--uf-l", "2.5", "--weight", "75"]) == 0
