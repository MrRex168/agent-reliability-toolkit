from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Iterator


_PREFIX = "agent_reliability."


def _set_attribute(span: Any, key: str, value: Any) -> None:
    if hasattr(span, "set_attribute"):
        span.set_attribute(key, value)


def _set_common_attributes(span: Any, attributes: dict[str, Any] | None) -> None:
    for key, value in (attributes or {}).items():
        name = key if key.startswith(_PREFIX) else f"{_PREFIX}{key}"
        _set_attribute(span, name, value)


@contextmanager
def trace_agent_run(
    tracer: Any,
    *,
    test_id: str | None = None,
    run_number: int | None = None,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any]:
    """Create an OpenTelemetry span for one agent execution.

    ``tracer`` is intentionally duck-typed, so OpenTelemetry remains optional.
    Toolkit-specific attributes are namespaced under ``agent_reliability.``.
    """
    span_attributes: dict[str, Any] = {}
    if test_id is not None:
        span_attributes["test_id"] = test_id
    if run_number is not None:
        span_attributes["run_number"] = run_number
    if attributes:
        span_attributes.update(attributes)

    with tracer.start_as_current_span("agent.run") as span:
        _set_common_attributes(span, span_attributes)
        try:
            yield span
        except Exception as exc:
            if hasattr(span, "record_exception"):
                span.record_exception(exc)
            if hasattr(span, "set_status"):
                try:
                    from opentelemetry.trace import Status, StatusCode
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                except ImportError:
                    pass
            raise


def record_evaluation(
    span: Any,
    *,
    success: bool,
    failure_count: int = 0,
    reliability_score: float | None = None,
    latency_ms: float | None = None,
    failure_categories: list[str] | None = None,
) -> None:
    """Attach an evaluation result to an existing agent span."""
    _set_attribute(span, f"{_PREFIX}success", success)
    _set_attribute(span, f"{_PREFIX}failure_count", failure_count)
    if reliability_score is not None:
        _set_attribute(span, f"{_PREFIX}reliability_score", reliability_score)
    if latency_ms is not None:
        _set_attribute(span, f"{_PREFIX}latency_ms", latency_ms)
    if failure_categories:
        _set_attribute(span, f"{_PREFIX}failure_categories", failure_categories)

    if hasattr(span, "add_event"):
        span.add_event(
            "agent.evaluation",
            {
                f"{_PREFIX}success": success,
                f"{_PREFIX}failure_count": failure_count,
            },
        )


def instrument_agent(
    agent: Any,
    *,
    tracer: Any | None = None,
    service_name: str = "agent-reliability",
    method: str = "run",
) -> Any:
    """Wrap an agent's run method with an OpenTelemetry span.

    If no tracer is supplied, the OpenTelemetry SDK is loaded lazily and a
    tracer is created from the global provider. Install the ``otel`` extra to
    use this convenience path.
    """
    if tracer is None:
        try:
            from opentelemetry import trace
        except ImportError as exc:
            raise RuntimeError(
                "OpenTelemetry is optional. Install with "
                "pip install -e '.[otel]' or pass a compatible tracer."
            ) from exc
        tracer = trace.get_tracer(service_name)

    original = getattr(agent, method)

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        with trace_agent_run(tracer):
            return original(*args, **kwargs)

    setattr(agent, method, wrapped)
    return agent


__all__ = ["instrument_agent", "record_evaluation", "trace_agent_run"]
