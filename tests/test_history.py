from __future__ import annotations

from agent_reliability.history import EvaluationHistory


def sample_report() -> dict:
    return {
        "task_success": 90.0,
        "consistency": 80.0,
        "reliability_score": 85.0,
        "runs": [
            {"test_id": "refund", "success": True},
            {"test_id": "refund", "success": False},
        ],
    }


def test_save_list_and_get(tmp_path):
    history = EvaluationHistory(tmp_path / "history.db")
    record_id = history.save(sample_report(), agent="demo-agent", version="1.2.0")

    records = history.list()
    assert len(records) == 1
    assert records[0].id == record_id
    assert records[0].agent == "demo-agent"
    assert records[0].version == "1.2.0"
    assert records[0].total_runs == 2
    assert records[0].failed_runs == 1
    assert history.get(record_id)["reliability_score"] == 85.0


def test_delete(tmp_path):
    history = EvaluationHistory(tmp_path / "history.db")
    record_id = history.save(sample_report())
    history.delete(record_id)

    assert history.list() == []


def test_missing_evaluation_raises(tmp_path):
    history = EvaluationHistory(tmp_path / "history.db")
    try:
        history.get(999)
    except KeyError as exc:
        assert "999" in str(exc)
    else:
        raise AssertionError("expected KeyError")
