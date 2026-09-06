from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class Judge(Protocol):
    """Provider-agnostic interface for semantic evaluation.

    A judge receives the agent output, the original input, and evaluation criteria,
    then returns a score from 0.0 to 1.0 plus a short explanation.
    """

    def judge(
        self, output: Any, input_text: str, criteria: list[str]
    ) -> tuple[float, str]: ...


@dataclass(frozen=True)
class JudgeResult:
    score: float
    explanation: str


class LLMJudgeEvaluator:
    """Semantic evaluator backed by a caller-supplied judge.

    The toolkit deliberately does not require an LLM provider. Pass any callable
    object implementing ``judge(output, input_text, criteria)``.
    """

    def __init__(self, judge: Judge):
        self.judge = judge

    def evaluate(
        self,
        output: Any,
        expected: dict[str, Any],
        *,
        input_text: str = "",
    ) -> tuple[bool, list[str]]:
        config = expected.get("judge")
        if not config:
            return True, []
        if not isinstance(config, dict):
            raise ValueError("'judge' must be a mapping")

        criteria = config.get("criteria", [])
        if isinstance(criteria, str):
            criteria = [criteria]
        if not criteria:
            raise ValueError("judge.criteria must contain at least one criterion")

        threshold = float(config.get("threshold", 0.8))
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("judge.threshold must be between 0 and 1")

        score, explanation = self.judge.judge(output, input_text, [str(c) for c in criteria])
        score = float(score)
        if not 0.0 <= score <= 1.0:
            raise ValueError("judge score must be between 0 and 1")

        if score < threshold:
            failures = [
                f"judge score {score:.2f} below threshold {threshold:.2f}: {explanation}"
            ]
            return False, failures
        return True, []
