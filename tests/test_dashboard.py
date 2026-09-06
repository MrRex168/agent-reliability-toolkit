from __future__ import annotations

import pytest

flask = pytest.importorskip("flask")

from agent_reliability.dashboard import create_app
from agent_reliability.history import EvaluationHistory


def report(success: bool = True) -> dict:
    return {
        "task_success": 100.0 if success else 50.0,
        "consistency": 100.0 if success else 0.0,
        "reliability_score": 100.0 if success else 25.0,
        "runs": [
            {
                "test_id": "refund",
                "run_number": 1,
                "success": success,
                "output": "Refunds are available within 30 days." if success else "Unknown",
                "latency_seconds": 0.01,
                "failure_categories": [] if success else [{"category": "OUTPUT_MISMATCH", "severity": "ERROR", "message": "missing expected text"}],
            }
        ],
    }


def test_dashboard_index_and_detail(tmp_path):
    history = EvaluationHistory(tmp_path / "history.db")
    first = history.save(report(), agent="demo-agent", version="1.0")
    second = history.save(report(False), agent="demo-agent", version="1.1")
    app = create_app(tmp_path / "history.db")
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert b"demo-agent" in response.data
    assert b"25.0" in response.data

    response = client.get(f"/evaluation/{second}")
    assert response.status_code == 200
    assert b"OUTPUT_MISMATCH" in response.data

    response = client.get(f"/compare/{first}/{second}")
    assert response.status_code == 200
    assert b"REGRESSION DETECTED" in response.data


def test_dashboard_api_and_missing_evaluation(tmp_path):
    history = EvaluationHistory(tmp_path / "history.db")
    record_id = history.save(report(), agent="api-agent")
    app = create_app(tmp_path / "history.db")
    client = app.test_client()

    response = client.get("/api/evaluations")
    assert response.status_code == 200
    assert response.json[0]["id"] == record_id

    response = client.get(f"/api/evaluations/{record_id}")
    assert response.status_code == 200
    assert response.json["reliability_score"] == 100.0

    assert client.get("/evaluation/999").status_code == 404
    assert client.get("/api/evaluations/999").status_code == 404
