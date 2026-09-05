from agent_reliability.regression import compare_reports


def _report(task_success: float, consistency: float, reliability: float, failures: int = 0):
    return {
        "task_success": task_success,
        "consistency": consistency,
        "reliability_score": reliability,
        "runs": [
            {"test_id": "a", "success": i >= failures}
            for i in range(4)
        ],
    }


def test_regression_detects_metric_drop():
    baseline = _report(100, 100, 100)
    current = _report(90, 100, 95)
    result = compare_reports(baseline, current)
    assert not result.passed
    assert any(c.metric == "task_success" and c.regressed for c in result.changes)


def test_regression_threshold_allows_small_drop():
    baseline = _report(100, 100, 100)
    current = _report(99, 100, 99.5)
    result = compare_reports(baseline, current, threshold=2.0)
    assert result.passed


def test_regression_detects_per_test_drop():
    baseline = _report(100, 100, 100)
    current = {
        "task_success": 75,
        "consistency": 100,
        "reliability_score": 87.5,
        "runs": [
            {"test_id": "a", "success": True},
            {"test_id": "a", "success": False},
            {"test_id": "a", "success": False},
            {"test_id": "a", "success": False},
        ],
    }
    result = compare_reports(baseline, current)
    assert not result.passed
    assert any(c.metric == "test:a" and c.regressed for c in result.changes)
