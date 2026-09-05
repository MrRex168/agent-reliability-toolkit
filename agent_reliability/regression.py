from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class RegressionChange:
    metric: str
    baseline: float
    current: float
    delta: float
    regressed: bool


@dataclass(frozen=True)
class RegressionReport:
    passed: bool
    threshold: float
    changes: list[RegressionChange]
    new_failures: int
    resolved_failures: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _test_success_rates(report: dict[str, Any]) -> dict[str, float]:
    totals: dict[str, list[int]] = {}
    for run in report.get("runs", []):
        test_id = str(run["test_id"])
        totals.setdefault(test_id, [0, 0])
        totals[test_id][1] += 1
        totals[test_id][0] += int(bool(run.get("success")))
    return {
        test_id: successful / total * 100
        for test_id, (successful, total) in totals.items()
        if total
    }


def compare_reports(
    baseline: dict[str, Any],
    current: dict[str, Any],
    threshold: float = 0.0,
) -> RegressionReport:
    """Compare two JSON evaluation reports and detect meaningful regressions."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    metrics = ("task_success", "consistency", "reliability_score")
    changes: list[RegressionChange] = []
    for metric in metrics:
        before = float(baseline.get(metric, 0.0))
        after = float(current.get(metric, 0.0))
        delta = after - before
        changes.append(RegressionChange(metric, before, after, delta, delta < -threshold))

    baseline_rates = _test_success_rates(baseline)
    current_rates = _test_success_rates(current)
    test_changes: list[RegressionChange] = []
    for test_id in sorted(set(baseline_rates) | set(current_rates)):
        before = baseline_rates.get(test_id, 0.0)
        after = current_rates.get(test_id, 0.0)
        delta = after - before
        if test_id in baseline_rates and test_id in current_rates:
            test_changes.append(RegressionChange(f"test:{test_id}", before, after, delta, delta < -threshold))

    changes.extend(test_changes)

    baseline_failed = sum(1 for run in baseline.get("runs", []) if not run.get("success"))
    current_failed = sum(1 for run in current.get("runs", []) if not run.get("success"))
    new_failures = max(0, current_failed - baseline_failed)
    resolved_failures = max(0, baseline_failed - current_failed)
    passed = not any(change.regressed for change in changes)

    return RegressionReport(passed, threshold, changes, new_failures, resolved_failures)
