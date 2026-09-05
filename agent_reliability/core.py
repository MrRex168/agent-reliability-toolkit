from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from .failures import Failure, classify_failures
from .tools import ToolTrace, evaluate_tool_calls


class Agent(Protocol):
    """Minimal interface an agent adapter needs to implement."""
    def run(self, prompt: str) -> Any: ...


class Evaluator(Protocol):
    """Protocol for pluggable evaluators."""
    def evaluate(self, output: Any, expected: dict[str, Any]) -> tuple[bool, list[str]]: ...


@dataclass
class RunResult:
    test_id: str
    run_number: int
    success: bool
    output: Any
    latency_seconds: float
    failures: list[str] = field(default_factory=list)
    failure_categories: list[Failure] = field(default_factory=list)


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


class BasicEvaluator:
    """Deterministic evaluator for text and structured agent outputs."""
    def evaluate(self, output: Any, expected: dict[str, Any]) -> tuple[bool, list[str]]:
        failures: list[str] = []
        for phrase in expected.get("contains", []):
            if str(phrase).lower() not in str(output).lower():
                failures.append(f"missing expected text: {phrase!r}")
        if "equals" in expected and output != expected["equals"]:
            failures.append(f"expected exact output {expected['equals']!r}, got {output!r}")
        if "json_equals" in expected:
            wanted = expected["json_equals"]
            if not isinstance(output, dict):
                failures.append("expected structured JSON output, got non-object output")
            elif output != wanted:
                failures.append(f"expected JSON {wanted!r}, got {output!r}")
        required_keys = expected.get("required_keys", [])
        if required_keys:
            if not isinstance(output, dict):
                failures.append("required_keys can only be checked against a structured object")
            else:
                for key in required_keys:
                    if key not in output:
                        failures.append(f"missing required key: {key!r}")
        return not failures, failures


ContainsEvaluator = BasicEvaluator


def evaluate_cases(agent: Agent, cases: list[dict[str, Any]], runs_per_test: int = 10, evaluator: Evaluator | None = None) -> EvaluationReport:
    """Run each test repeatedly and calculate reliability with failure diagnostics."""
    if runs_per_test < 1:
        raise ValueError("runs_per_test must be at least 1")
    evaluator = evaluator or BasicEvaluator()
    results: list[RunResult] = []

    for case in cases:
        test_id = str(case["id"])
        prompt = str(case.get("input", ""))
        expected = case.get("expected", {})
        for run_number in range(1, runs_per_test + 1):
            started = time.perf_counter()
            try:
                raw_output = agent.run(prompt)
                trace = raw_output if isinstance(raw_output, ToolTrace) else None
                output = trace.output if trace else raw_output
                success, failures = evaluator.evaluate(output, expected)
                if trace and (expected.get("tool_calls") or expected.get("tool_names")):
                    tool_success, tool_failures = evaluate_tool_calls(trace, expected)
                    success = success and tool_success
                    failures.extend(tool_failures)
            except Exception as exc:
                output = ""
                success = False
                failures = [f"agent error: {type(exc).__name__}: {exc}"]
            categories = classify_failures(failures)
            results.append(RunResult(test_id, run_number, success, output, time.perf_counter() - started, failures, categories))

    total = len(results)
    successful = sum(r.success for r in results)
    task_success = successful / total * 100 if total else 0.0
    consistent_tests = 0
    for case in cases:
        outcomes = [r.success for r in results if r.test_id == str(case["id"])]
        if outcomes and len(set(outcomes)) == 1:
            consistent_tests += 1
    consistency = consistent_tests / len(cases) * 100 if cases else 0.0
    average_latency = sum(r.latency_seconds for r in results) / total if total else 0.0
    reliability = (task_success + consistency) / 2
    return EvaluationReport(len(cases), runs_per_test, total, successful, total - successful, task_success, consistency, average_latency, reliability, results)
