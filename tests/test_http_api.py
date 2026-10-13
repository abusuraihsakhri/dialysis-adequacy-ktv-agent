"""HTTP integration smoke tests for the optional service."""
from fastapi.testclient import TestClient
from dialysis_adequacy_ktv_agent.server import create_app


def test_http_health_and_adequacy():
    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "HEALTHY"
        response = client.post("/api/adequacy", json={
            "pre_bun": 60, "post_bun": 15, "dialysis_time_hr": 4,
            "uf_volume_l": 2.5, "post_weight_kg": 75, "sessions_per_week": 3,
            "session_position": "midweek"
        })
        assert response.status_code == 200
        payload = response.json()
        assert payload["spktv"]["spktv"] > 1.2
        assert 0.8 < payload["npcr"]["npcr_g_kg_day"] < 1.4


def test_http_invalid_input_rejected():
    with TestClient(create_app()) as client:
        response = client.post("/api/adequacy", json={
            "pre_bun": 60, "post_bun": 15, "dialysis_time_hr": 4,
            "uf_volume_l": -1, "post_weight_kg": 75
        })
        assert response.status_code == 422


def test_http_rejects_simple_identifiers_in_legacy_audit():
    with TestClient(create_app()) as client:
        response = client.post("/api/audit", json={
            "case_id": "MRN-123456", "patient_synthetic_id": "synthetic",
            "primary_metric": 2, "secondary_metric": 1, "status_flag": "NOMINAL"
        })
        assert response.status_code == 400
