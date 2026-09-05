from agent_reliability.core import evaluate_cases


class StableAgent:
    def run(self, prompt: str) -> str:
        return "The answer is 42."


class FlakyAgent:
    def __init__(self):
        self.calls = 0

    def run(self, prompt: str) -> str:
        self.calls += 1
        return "The answer is 42." if self.calls % 2 else "I don't know."


def test_stable_agent_is_reliable():
    report = evaluate_cases(
        StableAgent(),
        [{"id": "answer", "input": "What is the answer?", "expected": {"contains": ["42"]}}],
        runs_per_test=4,
    )
    assert report.task_success == 100
    assert report.consistency == 100
    assert report.reliability_score == 100


def test_flaky_agent_exposes_inconsistency():
    report = evaluate_cases(
        FlakyAgent(),
        [{"id": "answer", "input": "What is the answer?", "expected": {"contains": ["42"]}}],
        runs_per_test=4,
    )
    assert report.task_success == 50
    assert report.consistency == 0
    assert report.reliability_score == 25
    assert report.failed == 2
