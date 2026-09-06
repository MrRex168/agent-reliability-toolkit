from __future__ import annotations

from agent_reliability.otel import instrument_agent, record_evaluation, trace_agent_run


class FakeSpan:
    def __init__(self) -> None:
        self.attributes = {}
        self.events = []
        self.exceptions = []

    def set_attribute(self, key, value):
        self.attributes[key] = value

    def add_event(self, name, attributes=None):
        self.events.append((name, attributes))

    def record_exception(self, exc):
        self.exceptions.append(exc)


class FakeSpanContext:
    def __init__(self, span):
        self.span = span

    def __enter__(self):
        return self.span

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeTracer:
    def __init__(self):
        self.spans = []

    def start_as_current_span(self, name):
        span = FakeSpan()
        span.name = name
        self.spans.append(span)
        return FakeSpanContext(span)


def test_trace_agent_run_records_namespaced_attributes():
    tracer = FakeTracer()

    with trace_agent_run(tracer, test_id="refund-policy", run_number=3) as span:
        span.set_attribute("agent_reliability.custom", "ok")

    assert tracer.spans[0].name == "agent.run"
    assert tracer.spans[0].attributes["agent_reliability.test_id"] == "refund-policy"
    assert tracer.spans[0].attributes["agent_reliability.run_number"] == 3


def test_record_evaluation_attaches_result_and_event():
    span = FakeSpan()

    record_evaluation(
        span,
        success=False,
        failure_count=2,
        reliability_score=72.5,
        latency_ms=184.2,
        failure_categories=["OUTPUT_MISMATCH", "TOOL_EXECUTION_ERROR"],
    )

    assert span.attributes["agent_reliability.success"] is False
    assert span.attributes["agent_reliability.failure_count"] == 2
    assert span.attributes["agent_reliability.reliability_score"] == 72.5
    assert span.attributes["agent_reliability.latency_ms"] == 184.2
    assert span.events[0][0] == "agent.evaluation"


def test_instrument_agent_wraps_run_method():
    class Agent:
        def run(self, prompt):
            return f"answer: {prompt}"

    tracer = FakeTracer()
    agent = instrument_agent(Agent(), tracer=tracer)

    assert agent.run("hello") == "answer: hello"
    assert len(tracer.spans) == 1
    assert tracer.spans[0].name == "agent.run"


def test_trace_agent_run_records_exception():
    tracer = FakeTracer()

    try:
        with trace_agent_run(tracer):
            raise ValueError("boom")
    except ValueError:
        pass

    assert len(tracer.spans[0].exceptions) == 1
    assert str(tracer.spans[0].exceptions[0]) == "boom"
