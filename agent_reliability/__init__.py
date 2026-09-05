"""AI Agent Reliability Toolkit."""

from .core import Agent, EvaluationReport, Evaluator, evaluate_cases
from .failures import Failure, FailureCategory, classify_failure, classify_failures
from .regression import RegressionChange, RegressionReport, compare_reports
from .tools import ToolCall, ToolRecorder, ToolTrace, evaluate_tool_calls

__all__ = [
    "Agent",
    "EvaluationReport",
    "Evaluator",
    "Failure",
    "FailureCategory",
    "RegressionChange",
    "RegressionReport",
    "ToolCall",
    "ToolRecorder",
    "ToolTrace",
    "classify_failure",
    "classify_failures",
    "compare_reports",
    "evaluate_cases",
    "evaluate_tool_calls",
]
__version__ = "0.4.0"
