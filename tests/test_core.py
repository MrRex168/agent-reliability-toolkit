from agent_reliability.core import evaluate_cases
from agent_reliability.failures import FailureCategory, classify_failure
from agent_reliability.tools import ToolCall, ToolTrace


class StableAgent:
    def run(self, prompt: str) -> str:
        return "The answer is 42."


class FlakyAgent:
    def __init__(self):
        self.calls = 0

    def run(self, prompt: str) -> str:
        self.calls += 1
        return "The answer is 42." if self.calls % 2 else "I don't know."


class StructuredAgent:
    def run(self, prompt: str) -> dict:
        return {"answer": "42", "confidence": 0.95}


class ToolAgent:
    def run(self, prompt: str) -> ToolTrace:
        return ToolTrace(
            output="Order 1234 is shipped.",
            calls=[ToolCall(name="search_orders", arguments={"order_id": "1243"})],
        )


def test_stable_agent_is_reliable():
    report = evaluate_cases(StableAgent(), [{"id": "answer", "input": "What is the answer?", "expected": {"contains": ["42"]}}], runs_per_test=4)
    assert report.task_success == 100
    assert report.consistency == 100
    assert report.reliability_score == 100


def test_flaky_agent_exposes_inconsistency():
    report = evaluate_cases(FlakyAgent(), [{"id": "answer", "input": "What is the answer?", "expected": {"contains": ["42"]}}], runs_per_test=4)
    assert report.task_success == 50
    assert report.consistency == 0
    assert report.reliability_score == 25
    assert report.failed == 2
    assert report.runs[1].failure_categories[0].category == FailureCategory.OUTPUT_MISMATCH


def test_structured_output_required_keys():
    report = evaluate_cases(StructuredAgent(), [{"id": "structured", "input": "Return data", "expected": {"required_keys": ["answer", "confidence"]}}], runs_per_test=2)
    assert report.task_success == 100


def test_structured_output_exact_match():
    report = evaluate_cases(StructuredAgent(), [{"id": "structured", "input": "Return data", "expected": {"json_equals": {"answer": "42", "confidence": 0.95}}}], runs_per_test=2)
    assert report.task_success == 100


def test_tool_selection_and_argument_failures_are_classified():
    report = evaluate_cases(
        ToolAgent(),
        [{
            "id": "order-status",
            "input": "Where is order 1234?",
            "expected": {
                "tool_calls": [{"name": "get_order", "arguments": {"order_id": "1234"}}],
                "tool_call_mode": "exact",
            },
        }],
        runs_per_test=1,
    )
    categories = {failure.category for failure in report.runs[0].failure_categories}
    assert FailureCategory.TOOL_SELECTION_ERROR in categories
    assert FailureCategory.TOOL_ARGUMENT_ERROR in categories


def test_failure_classifier_handles_agent_errors():
    failure = classify_failure("agent error: TimeoutError: request timed out")
    assert failure.category == FailureCategory.AGENT_ERROR
    assert failure.severity == "HIGH"
