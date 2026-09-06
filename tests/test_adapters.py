from __future__ import annotations

from dataclasses import dataclass

import pytest

from agent_reliability.adapters import LangChainAdapter, LangGraphAdapter
from agent_reliability.core import evaluate_cases


@dataclass
class Message:
    content: str


class FakeRunnable:
    def invoke(self, prompt: str):
        return Message(f"received: {prompt}")


class FakeGraph:
    def invoke(self, state):
        prompt = state["messages"][0]["content"]
        return {"messages": [Message(f"answer: {prompt}")]}


def test_langchain_adapter_normalizes_message_output():
    adapter = LangChainAdapter(FakeRunnable())
    assert adapter.run("hello") == "received: hello"


def test_langgraph_adapter_builds_messages_and_normalizes_output():
    adapter = LangGraphAdapter(FakeGraph())
    assert adapter.run("hello") == "answer: hello"


def test_adapters_work_with_evaluation_engine():
    report = evaluate_cases(
        LangChainAdapter(FakeRunnable()),
        [{"id": "reply", "input": "hello", "expected": {"contains": ["received"]}}],
        runs_per_test=2,
    )
    assert report.successful == 2


def test_langgraph_custom_input_and_output_parsers():
    adapter = LangGraphAdapter(
        FakeGraph(),
        input_builder=lambda prompt: {"messages": [{"role": "user", "content": prompt.upper()}]},
        output_parser=lambda state: state["messages"][-1].content.upper(),
    )
    assert adapter.run("hello") == "ANSWER: HELLO"


@pytest.mark.parametrize("adapter_cls", [LangChainAdapter, LangGraphAdapter])
def test_adapter_requires_invoke(adapter_cls):
    with pytest.raises(TypeError, match="invoke"):
        adapter_cls(object())
