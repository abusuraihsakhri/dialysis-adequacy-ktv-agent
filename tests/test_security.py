"""
Security-focused tests for Dialysis Adequacy Ktv Agent.
Tests PHI guard, audit trail, and security configuration.
"""
import sys
import os
import warnings
from pathlib import Path

# Set a test audit key to suppress ephemeral key warning
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-test-suite")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import (
    PHIGuard,
    AuditLogger,
    AuditTrail,
    SecurityException,
    assert_no_phi,
)


class TestPHIGuard:
    """Test PHI detection and redaction."""

    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive")

    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_dob_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1980")

    def test_patient_name_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Kt/V calculation result: 1.4")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")

    def test_redact_phi(self):
        redacted = PHIGuard.redact_phi("Patient MRN-12345 has SSN 123-45-6789")
        assert "MRN" not in redacted or "REDACTED" in redacted
        assert "123-45-6789" not in redacted

    def test_redact_preserves_clean_text(self):
        clean = "Kt/V result: 1.4, URR: 75%"
        assert PHIGuard.redact_phi(clean) == clean


class TestAuditTrail:
    """Test HMAC-SHA256 audit trail integrity."""

    def test_explicit_key(self):
        trail = AuditTrail(secret_key="test-key-123")
        entry = trail.log("test", "tier1", "TEST_EVENT", {"data": "value"})
        assert entry["current_hash"] != ""
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_chained_integrity(self):
        trail = AuditTrail(secret_key="test-key-456")
        trail.log("actor1", "tier1", "EVENT_A", {"x": 1})
        trail.log("actor2", "tier2", "EVENT_B", {"y": 2})
        trail.log("actor3", "tier1", "EVENT_C", {"z": 3})
        assert trail.verify_integrity() is True

    def test_tamper_detection(self):
        trail = AuditTrail(secret_key="test-key-789")
        trail.log("actor1", "tier1", "EVENT_A", {"x": 1})
        trail.log("actor2", "tier2", "EVENT_B", {"y": 2})
        # Tamper with the first entry's current_hash (breaks chain)
        trail.logs[0]["current_hash"] = "tampered_hash"
        assert trail.verify_integrity() is False

    def test_ephemeral_key_warning(self):
        """When no key is provided, a warning should be issued."""
        # Ensure env var is not set
        old_key = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                trail = AuditTrail()
                assert len(w) == 1
                assert "AUDIT_SECRET_KEY" in str(w[0].message)
        finally:
            if old_key:
                os.environ["AUDIT_SECRET_KEY"] = old_key

    def test_phi_blocked_in_audit(self):
        trail = AuditTrail(secret_key="test-key-000")
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"data": "Patient MRN-12345"})


class TestCalculationEdgeCases:
    """Edge case tests for calculation functions."""

    def test_spktv_very_low_r_ratio(self):
        """Very low R ratio (excellent dialysis) should give high Kt/V."""
        from ktv_sentinel import calc_spktv
        r = calc_spktv(80, 10, 4, 3.0, 70)
        assert r["spktv"] > 1.5
        assert r["adequate"] is True

    def test_urr_zero_post_bun(self):
        """Zero post-BUN gives 100% URR."""
        from ktv_sentinel import calc_urr
        r = calc_urr(60, 0)
        assert r["urr_percent"] == 100.0
        assert r["adequate"] is True

    def test_ektv_negative_spktv_recovery(self):
        """eKt/V should be lower than spKt/V for short sessions."""
        from ktv_sentinel import calc_ektv
        r = calc_ektv(1.0, 2.0)
        assert r["ektv"] < 1.0

    def test_stdktv_higher_frequency_higher_value(self):
        """More sessions per week should yield higher stdKt/V."""
        from ktv_sentinel import calc_stdktv
        r_6x = calc_stdktv(1.4, 6, 2.5)
        r_3x = calc_stdktv(1.4, 3, 4)
        # With more frequent sessions, stdKt/V should be higher
        assert r_6x["stdktv"] >= r_3x["stdktv"]

    def test_stdktv_more_sessions_non_lower(self):
        """Increasing session count should not decrease stdKt/V."""
        from ktv_sentinel import calc_stdktv
        r_3x = calc_stdktv(1.2, 3, 4)
        r_4x = calc_stdktv(1.2, 4, 4)
        assert r_4x["stdktv"] >= r_3x["stdktv"]

    def test_npcr_low_weight(self):
        """Low weight patient with same BUN values."""
        from ktv_sentinel import calc_nPCR
        r = calc_nPCR(60, 15, 4, 1.5, 45)
        assert r["npcr_g_kg_day"] > 0
        assert r["status"] in ("low", "adequate", "high")
