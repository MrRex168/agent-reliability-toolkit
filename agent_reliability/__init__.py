"""AI Agent Reliability Toolkit."""

from .core import Agent, BasicEvaluator, EvaluationReport, Evaluator, evaluate_cases
from .failures import Failure, FailureCategory, classify_failure, classify_failures
from .judge import Judge, JudgeResult, LLMJudgeEvaluator
from .regression import RegressionChange, RegressionReport, compare_reports
from .tools import ToolCall, ToolRecorder, ToolTrace, evaluate_tool_calls
from .adapters import LangChainAdapter, LangGraphAdapter, MCPTraceAdapter, normalize_mcp_call

__all__ = [
    "Agent",
    "BasicEvaluator",
    "EvaluationReport",
    "Evaluator",
    "Failure",
    "FailureCategory",
    "Judge",
    "JudgeResult",
    "LLMJudgeEvaluator",
    "LangChainAdapter",
    "LangGraphAdapter",
    "MCPTraceAdapter",
    "normalize_mcp_call",
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
__version__ = "0.6.0"
