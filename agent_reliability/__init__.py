"""AI Agent Reliability Toolkit."""

from .core import Agent, BasicEvaluator, EvaluationReport, Evaluator, evaluate_cases
from .failures import Failure, FailureCategory, classify_failure, classify_failures
from .history import EvaluationHistory, EvaluationRecord
from .judge import Judge, JudgeResult, LLMJudgeEvaluator
from .otel import instrument_agent, record_evaluation, trace_agent_run
from .regression import RegressionChange, RegressionReport, compare_reports
from .tools import ToolCall, ToolRecorder, ToolTrace, evaluate_tool_calls
from .adapters import LangChainAdapter, LangGraphAdapter, MCPTraceAdapter, normalize_mcp_call
from .dashboard import create_app, run_dashboard

__all__ = [
    "Agent", "BasicEvaluator", "EvaluationReport", "Evaluator",
    "Failure", "FailureCategory", "Judge", "JudgeResult", "LLMJudgeEvaluator",
    "EvaluationHistory", "EvaluationRecord",
    "LangChainAdapter", "LangGraphAdapter", "MCPTraceAdapter", "normalize_mcp_call",
    "instrument_agent", "record_evaluation", "trace_agent_run",
    "RegressionChange", "RegressionReport", "compare_reports",
    "ToolCall", "ToolRecorder", "ToolTrace",
    "create_app", "run_dashboard",
    "classify_failure", "classify_failures", "evaluate_cases", "evaluate_tool_calls",
]
__version__ = "1.0.0"
