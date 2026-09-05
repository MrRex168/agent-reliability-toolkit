from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

import yaml

from .core import evaluate_cases


def _load_symbol(spec: str) -> Any:
    module_name, symbol = spec.split(":", 1)
    return getattr(importlib.import_module(module_name), symbol)


def _load_cases(path: Path) -> tuple[Any, list[dict[str, Any]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        agent_spec = data.get("agent")
        cases = data.get("cases", [])
    else:
        agent_spec = None
        cases = data or []
    if not agent_spec:
        raise ValueError("Test file must define an 'agent: module:symbol' entry")
    if not isinstance(cases, list):
        raise ValueError("'cases' must be a YAML list")
    return _load_symbol(agent_spec), cases


def _print_report(report) -> None:
    print("\nAI Agent Reliability Report")
    print("───────────────────────────")
    print(f"Tests             {report.tests}")
    print(f"Runs per test     {report.runs_per_test}")
    print(f"Total runs        {report.total_runs}")
    print(f"Successful        {report.successful}")
    print(f"Failed            {report.failed}")
    print()
    print(f"Task success      {report.task_success:.1f}%")
    print(f"Consistency       {report.consistency:.1f}%")
    print(f"Avg latency       {report.average_latency_seconds:.3f}s")
    print(f"Reliability       {report.reliability_score:.1f}/100")

    failures = [r for r in report.runs if not r.success]
    if failures:
        print("\nFailure Analysis")
        for result in failures:
            print(f"\n  {result.test_id} — run {result.run_number}")
            for failure in result.failure_categories:
                print(f"    [{failure.severity}] {failure.category.value}: {failure.message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate AI agent reliability through repeated tests.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    eval_parser = subparsers.add_parser("eval", help="Run an evaluation")
    eval_parser.add_argument("file", type=Path, help="YAML evaluation file")
    eval_parser.add_argument("--runs", type=int, default=10, help="Runs per test case (default: 10)")
    eval_parser.add_argument("--json", dest="json_path", type=Path, help="Write the full report as JSON")
    args = parser.parse_args()

    if args.command == "eval":
        agent, cases = _load_cases(args.file)
        report = evaluate_cases(agent, cases, runs_per_test=args.runs)
        _print_report(report)
        if args.json_path:
            args.json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
            print(f"\nJSON report written to {args.json_path}")


if __name__ == "__main__":
    main()
