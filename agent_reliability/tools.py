from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolCall:
    """A normalized record of one tool invocation made by an agent."""
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = True


@dataclass
class ToolTrace:
    """Execution trace returned by an instrumented agent."""
    output: Any
    calls: list[ToolCall] = field(default_factory=list)


class ToolRecorder:
    """Wrap tool functions and record every invocation."""

    def __init__(self, tools: dict[str, Callable[..., Any]]):
        self.tools = tools
        self.calls: list[ToolCall] = []

    def call(self, name: str, **arguments: Any) -> Any:
        if name not in self.tools:
            raise KeyError(f"unknown tool: {name}")
        call = ToolCall(name=name, arguments=arguments)
        try:
            call.result = self.tools[name](**arguments)
            return call.result
        except Exception:
            call.success = False
            raise
        finally:
            self.calls.append(call)


def evaluate_tool_calls(trace: ToolTrace, expected: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate expected tool names and argument values against an execution trace."""
    failures: list[str] = []
    actual = trace.calls

    expected_tools = expected.get("tool_calls", [])
    if expected_tools:
        if expected.get("tool_call_mode", "contains") == "exact" and len(actual) != len(expected_tools):
            failures.append(f"expected exactly {len(expected_tools)} tool calls, got {len(actual)}")

        for index, wanted in enumerate(expected_tools, start=1):
            if index > len(actual):
                failures.append(f"missing expected tool call #{index}: {wanted.get('name')!r}")
                continue
            got = actual[index - 1]
            if got.name != wanted.get("name"):
                failures.append(f"tool call #{index}: expected {wanted.get('name')!r}, got {got.name!r}")
            for key, value in wanted.get("arguments", {}).items():
                if got.arguments.get(key) != value:
                    failures.append(
                        f"tool call #{index} argument {key!r}: expected {value!r}, got {got.arguments.get(key)!r}"
                    )

    expected_any = expected.get("tool_names", [])
    if expected_any:
        actual_names = [call.name for call in actual]
        for name in expected_any:
            if name not in actual_names:
                failures.append(f"expected tool was not called: {name!r}")

    failed_calls = [call.name for call in actual if not call.success]
    for name in failed_calls:
        failures.append(f"tool call failed: {name!r}")

    return not failures, failures
