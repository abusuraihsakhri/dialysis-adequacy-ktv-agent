"""Optional HTTP API; no API server is required for GitHub Pages."""
import json
from typing import Any, Dict
from pydantic import BaseModel, Field
from .models import ClinicalCasePayload
from .agents import DialysisCoordinator
from ktv_sentinel import full_adequacy_assessment
from agents.base import PHIGuard, SecurityException

coordinator = DialysisCoordinator()


class AdequacyRequest(BaseModel):
    pre_bun: float
    post_bun: float
    dialysis_time_hr: float
    uf_volume_l: float
    post_weight_kg: float
    sessions_per_week: int = Field(default=3, ge=1, le=7)
    session_position: str = "midweek"


class AuditRequest(BaseModel):
    case_id: str = "CASE-2026-001"
    patient_synthetic_id: str = "SYNTH-PT-881"
    primary_metric: float = 24.5
    secondary_metric: float = 14.0
    status_flag: str = "DISCORDANT"
    is_stat: bool = True
    clinical_notes: str = ""
    biomarkers: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    query: str


def create_app():
    from fastapi import FastAPI, HTTPException
    app = FastAPI(title="Dialysis adequacy calculator and legacy rule-based audit",
                  description="Experimental estimates; not clinical decision support",
                  version="2.0.1")

    @app.get("/health")
    def health():
        return {"status": "HEALTHY", "system": "dialysis-adequacy-ktv-agent", "version": "2.0.1"}

    @app.post("/api/adequacy")
    def api_adequacy(req: AdequacyRequest):
        try:
            return full_adequacy_assessment(
                req.pre_bun, req.post_bun, req.dialysis_time_hr,
                req.uf_volume_l, req.post_weight_kg, req.sessions_per_week,
                req.session_position
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/audit")
    def api_audit(req: AuditRequest):
        # This legacy audit uses demonstration thresholds, NOT dialysis adequacy rules.
        try:
            for text in (req.case_id, req.patient_synthetic_id,
                         req.status_flag, req.clinical_notes,
                         json.dumps(req.biomarkers)):
                PHIGuard.assert_no_phi(text)
        except SecurityException:
            raise HTTPException(status_code=400, detail="Potential identifier detected")
        payload = ClinicalCasePayload(
            case_id=req.case_id, patient_synthetic_id=req.patient_synthetic_id,
            primary_metric=req.primary_metric, secondary_metric=req.secondary_metric,
            status_flag=req.status_flag, is_stat=req.is_stat,
            clinical_notes=req.clinical_notes, biomarkers=req.biomarkers
        )
        return coordinator.process_case(payload)

    @app.post("/api/chat")
    def api_chat(req: ChatRequest):
        try:
            PHIGuard.assert_no_phi(req.query)
        except SecurityException:
            raise HTTPException(status_code=400, detail="Potential identifier detected")
        return {"response": coordinator.query_supervisory_chat(req.query)}

    return app
