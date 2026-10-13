"""
Clinical Algorithmic Engine & Guideline Rules for KtV-Sentinel: Hemodialysis Single-Pool & Equilibrated Kt/V Adequacy Agent.
Domain: Nephrology
Standard: nonclinical demonstration rules
"""
import math
from typing import Dict, Any, List, Optional
from .models import ClinicalCasePayload, AgentAlert, UrgencyLevel, ClinicalIntegrityStatus


class ClinicalDomainEngine:
    GUIDELINE = "nonclinical demonstration rules"
    PRIMARY_BASELINE_LIMIT = 20.0  # demonstration only; not a Kt/V threshold
    SECONDARY_ALERT_LIMIT = 10.0  # demonstration only

    @classmethod
    def evaluate_primary_index(cls, value: float) -> Optional[Dict[str, Any]]:
        if value > cls.PRIMARY_BASELINE_LIMIT:
            return {
                "title": "Primary Metric Threshold Exceeded",
                "finding": f"Observed value ({value:.2f}) exceeds nonclinical demonstration rules clinical baseline limit ({cls.PRIMARY_BASELINE_LIMIT:.1f}).",
                "recommendation": "Demonstration flag; interpret the underlying metric using its actual units.",
            }
        return None

    @classmethod
    def evaluate_secondary_kinetics(cls, value: float, is_stat: bool) -> Optional[Dict[str, Any]]:
        if value > cls.SECONDARY_ALERT_LIMIT or is_stat:
            return {
                "title": "STAT Kinetic Escalation Triggered",
                "finding": f"Kinetic parameter ({value:.2f}) with STAT={is_stat} requires prioritized supervision.",
                "recommendation": "Flag set by the caller; not an automated clinical emergency assessment.",
            }
        return None

    @classmethod
    def evaluate_biomarker_concordance(cls, status_flag: str, biomarkers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        status_upper = str(status_flag).upper()
        if "DISCORDANT" in status_upper or "EQUIVOCAL" in status_upper or "MUTANT" in status_upper:
            return {
                "title": "Phenotypic / Biomarker Discordance Identified",
                "finding": f"Status flag '{status_flag}' indicates divergence from standard diagnostic concordance.",
                "recommendation": f"Review the descriptive status flag; this is not a diagnostic rule.",
            }
        return None
