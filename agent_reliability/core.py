from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


class Agent(Protocol):
    """Minimal interface an agent adapter needs to implement."""

    def run(self, prompt: str) -> str: ...


class Evaluator(Protocol):
    """Protocol for pluggable evaluators."""

    def evaluate(self, output: str, expected: dict[str, Any]) -> tuple[bool, list[str]]: ...


@dataclass
class RunResult:
    test_id: str
    run_number: int
    success: bool
    output: str
    latency_seconds: float
    failures: list[str] = field(default_factory=list)


@dataclass
class EvaluationReport:
    tests: int
    runs_per_test: int
    total_runs: int
    successful: int
    failed: int
    task_success: float
    consistency: float
    average_latency_seconds: float
    reliability_score: float
    runs: list[RunResult]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContainsEvaluator:
    def evaluate(self, output: str, expected: dict[str, Any]) -> tuple[bool, list[str]]:
        failures: list[str] = []
        for phrase in expected.get("contains", []):
            if str(phrase).lower() not in output.lower():
                failures.append(f"missing expected text: {phrase!r}")
        return not failures, failures


def evaluate_cases(
    agent: Agent,
    cases: list[dict[str, Any]],
    runs_per_test: int = 10,
    evaluator: Evaluator | None = None,
) -> EvaluationReport:
    """Run each test case repeatedly and calculate baseline reliability metrics."""
    if runs_per_test < 1:
        raise ValueError("runs_per_test must be at least 1")
    evaluator = evaluator or ContainsEvaluator()
    results: list[RunResult] = []

    for case in cases:
        test_id = str(case["id"])
        prompt = str(case.get("input", ""))
        expected = case.get("expected", {})
        for run_number in range(1, runs_per_test + 1):
            started = time.perf_counter()
            try:
                output = str(agent.run(prompt))
                success, failures = evaluator.evaluate(output, expected)
            except Exception as exc:  # Agent failures are evaluation results, not evaluator crashes.
                output = ""
                success = False
                failures = [f"agent error: {type(exc).__name__}: {exc}"]
            latency = time.perf_counter() - started
            results.append(RunResult(test_id, run_number, success, output, latency, failures))

    total = len(results)
    successful = sum(r.success for r in results)
    task_success = (successful / total * 100) if total else 0.0

    # A test is consistent when every repeated run has the same pass/fail outcome.
    consistent_tests = 0
    for case in cases:
        outcomes = [r.success for r in results if r.test_id == str(case["id"])]
        if outcomes and len(set(outcomes)) == 1:
            consistent_tests += 1
    consistency = (consistent_tests / len(cases) * 100) if cases else 0.0
    average_latency = sum(r.latency_seconds for r in results) / total if total else 0.0
    reliability = (task_success + consistency) / 2

    return EvaluationReport(
        tests=len(cases),
        runs_per_test=runs_per_test,
        total_runs=total,
        successful=successful,
        failed=total - successful,
        task_success=task_success,
        consistency=consistency,
        average_latency_seconds=average_latency,
        reliability_score=reliability,
        runs=results,
    )
