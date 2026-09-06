from __future__ import annotations

from typing import Any, Callable


class LangChainAdapter:
    """Adapt a LangChain Runnable/agent to the toolkit's ``agent.run`` contract.

    The adapter intentionally does not import LangChain, so the core package keeps
    zero framework dependencies. Any object exposing ``invoke(input)`` works.
    """

    def __init__(
        self,
        runnable: Any,
        *,
        output_parser: Callable[[Any], Any] | None = None,
    ) -> None:
        if not hasattr(runnable, "invoke"):
            raise TypeError("runnable must expose an invoke(input) method")
        self.runnable = runnable
        self.output_parser = output_parser or self._default_output_parser

    def run(self, prompt: str) -> Any:
        return self.output_parser(self.runnable.invoke(prompt))

    @staticmethod
    def _default_output_parser(result: Any) -> Any:
        """Normalize common LangChain message/string outputs without hiding data."""
        if isinstance(result, str):
            return result
        content = getattr(result, "content", None)
        if content is not None:
            return content
        if isinstance(result, dict) and "output" in result:
            return result["output"]
        return result
