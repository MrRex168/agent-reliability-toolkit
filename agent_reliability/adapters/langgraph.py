from __future__ import annotations

from typing import Any, Callable


class LangGraphAdapter:
    """Adapt a compiled LangGraph graph to the toolkit's ``agent.run`` contract.

    LangGraph graphs expose ``invoke(input)``. The adapter accepts a custom
    output parser because graph state is application-specific.
    """

    def __init__(
        self,
        graph: Any,
        *,
        input_builder: Callable[[str], Any] | None = None,
        output_parser: Callable[[Any], Any] | None = None,
    ) -> None:
        if not hasattr(graph, "invoke"):
            raise TypeError("graph must expose an invoke(input) method")
        self.graph = graph
        self.input_builder = input_builder or (lambda prompt: {"messages": [{"role": "user", "content": prompt}]})
        self.output_parser = output_parser or self._default_output_parser

    def run(self, prompt: str) -> Any:
        state = self.graph.invoke(self.input_builder(prompt))
        return self.output_parser(state)

    @staticmethod
    def _default_output_parser(state: Any) -> Any:
        if isinstance(state, str):
            return state
        if isinstance(state, dict):
            messages = state.get("messages")
            if messages:
                last = messages[-1]
                content = getattr(last, "content", None)
                if content is not None:
                    return content
                if isinstance(last, dict) and "content" in last:
                    return last["content"]
            for key in ("output", "answer", "response"):
                if key in state:
                    return state[key]
        return state
