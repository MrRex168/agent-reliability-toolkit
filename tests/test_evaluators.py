from agent_reliability.core import BasicEvaluator, evaluate_cases
from agent_reliability.judge import LLMJudgeEvaluator


class RegexAgent:
    def run(self, prompt: str) -> str:
        return "Order 1234 is shipped."


class FakeJudge:
    def __init__(self, score: float, explanation: str = "Looks correct."):
        self.score = score
        self.explanation = explanation
        self.calls = []

    def judge(self, output, input_text, criteria):
        self.calls.append((output, input_text, criteria))
        return self.score, self.explanation


def test_regex_evaluator_matches_case_insensitively():
    evaluator = BasicEvaluator()
    success, failures = evaluator.evaluate(
        "Order 1234 is shipped.",
        {"regex": [r"order \d+ is shipped\.?"]},
    )
    assert success
    assert failures == []


def test_regex_evaluator_reports_mismatch():
    evaluator = BasicEvaluator()
    success, failures = evaluator.evaluate(
        "Order 1234 is pending.",
        {"regex": [r"order \d+ is shipped"]},
    )
    assert not success
    assert "regex did not match" in failures[0]


def test_regex_invalid_pattern_is_reported():
    evaluator = BasicEvaluator()
    success, failures = evaluator.evaluate("hello", {"regex": ["["]})
    assert not success
    assert "invalid regex" in failures[0]


def test_llm_judge_passes_above_threshold():
    judge = FakeJudge(0.92)
    evaluator = BasicEvaluator(LLMJudgeEvaluator(judge))
    success, failures = evaluator.evaluate(
        "The refund is available within 30 days.",
        {"judge": {"criteria": ["The answer is accurate and directly answers the question."], "threshold": 0.8}},
        input_text="What is the refund policy?",
    )
    assert success
    assert failures == []
    assert judge.calls[0][1] == "What is the refund policy?"


def test_llm_judge_fails_below_threshold():
    judge = FakeJudge(0.55, "The answer is incomplete.")
    evaluator = BasicEvaluator(LLMJudgeEvaluator(judge))
    success, failures = evaluator.evaluate(
        "I am not sure.",
        {"judge": {"criteria": ["The answer should resolve the user's question."], "threshold": 0.8}},
        input_text="What is the refund policy?",
    )
    assert not success
    assert "0.55" in failures[0]


def test_llm_judge_works_through_repeated_evaluation():
    judge = FakeJudge(1.0)
    report = evaluate_cases(
        RegexAgent(),
        [{
            "id": "semantic-answer",
            "input": "Where is order 1234?",
            "expected": {
                "judge": {
                    "criteria": ["The response correctly answers the order-status question."],
                    "threshold": 0.8,
                }
            },
        }],
        runs_per_test=3,
        evaluator=BasicEvaluator(LLMJudgeEvaluator(judge)),
    )
    assert report.task_success == 100
    assert len(judge.calls) == 3
