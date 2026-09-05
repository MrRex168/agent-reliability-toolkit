from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureCategory(str, Enum):
    AGENT_ERROR = "AGENT_ERROR"
    OUTPUT_MISMATCH = "OUTPUT_MISMATCH"
    STRUCTURED_OUTPUT_ERROR = "STRUCTURED_OUTPUT_ERROR"
    TOOL_SELECTION_ERROR = "TOOL_SELECTION_ERROR"
    TOOL_ARGUMENT_ERROR = "TOOL_ARGUMENT_ERROR"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Failure:
    category: FailureCategory
    message: str
    severity: str = "MEDIUM"


def classify_failure(message: str) -> Failure:
    """Classify a deterministic evaluator failure into a useful diagnostic category."""
    text = message.lower()
    if text.startswith("agent error:"):
        return Failure(FailureCategory.AGENT_ERROR, message, "HIGH")
    if "tool call failed" in text:
        return Failure(FailureCategory.TOOL_EXECUTION_ERROR, message, "HIGH")
    if "expected tool" in text or "missing expected tool call" in text:
        return Failure(FailureCategory.TOOL_SELECTION_ERROR, message, "HIGH")
    if "tool call #" in text and "argument" in text:
        return Failure(FailureCategory.TOOL_ARGUMENT_ERROR, message, "HIGH")
    if "structured json" in text or "required key" in text or "expected json" in text:
        return Failure(FailureCategory.STRUCTURED_OUTPUT_ERROR, message, "HIGH")
    if "missing expected text" in text or "expected exact output" in text:
        return Failure(FailureCategory.OUTPUT_MISMATCH, message, "MEDIUM")
    return Failure(FailureCategory.UNKNOWN, message, "MEDIUM")


def classify_failures(messages: list[str]) -> list[Failure]:
    return [classify_failure(message) for message in messages]
