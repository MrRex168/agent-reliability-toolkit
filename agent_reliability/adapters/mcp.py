from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from ..tools import ToolCall, ToolTrace


def _read(value: Any, *names: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default


def normalize_mcp_call(record: Any) -> ToolCall:
    """Normalize a generic MCP-style tool-call record into ``ToolCall``.

    The adapter intentionally uses duck typing so the core toolkit does not
    depend on a particular MCP SDK version. Records may be dictionaries or
    objects exposing common MCP fields such as ``name``, ``arguments``,
    ``result``/``content``, and ``error``.
    """
    name = _read(record, "name", "tool_name", "tool", default="")
    arguments = _read(record, "arguments", "args", "input", default={}) or {}
    result = _read(record, "result", "output", "content", default=None)
    error = _read(record, "error", "exception", default=None)
    success = _read(record, "success", "ok", default=None)
    if success is None:
        success = error is None

    if not isinstance(arguments, dict):
        try:
            arguments = dict(arguments)
        except (TypeError, ValueError):
            arguments = {"value": arguments}

    if error is not None and result is None:
        result = str(error)

    return ToolCall(
        name=str(name),
        arguments=arguments,
        result=result,
        success=bool(success),
    )


class MCPTraceAdapter:
    """Wrap an MCP-capable callable and return a normalized ``ToolTrace``.

    ``runner`` is application-owned. It receives the prompt and may return a
    ``ToolTrace`` directly, a mapping/object containing ``output`` and
    ``tool_calls``/``calls``, or an iterable of MCP-style call records.
    """

    def __init__(
        self,
        runner: Callable[[str], Any],
        *,
        output_parser: Callable[[Any], Any] | None = None,
        calls_parser: Callable[[Any], Iterable[Any]] | None = None,
    ) -> None:
        self.runner = runner
        self.output_parser = output_parser
        self.calls_parser = calls_parser

    def run(self, prompt: str) -> ToolTrace:
        raw = self.runner(prompt)
        if isinstance(raw, ToolTrace):
            return raw

        output = _read(raw, "output", "text", "answer", default=None)
        raw_calls = _read(raw, "tool_calls", "calls", "trace", default=None)

        if self.calls_parser is not None:
            raw_calls = self.calls_parser(raw)

        if raw_calls is None and isinstance(raw, (list, tuple)):
            raw_calls = raw

        calls = [normalize_mcp_call(call) for call in (raw_calls or [])]
        if output is None and not calls:
            output = raw
        if self.output_parser is not None:
            output = self.output_parser(raw)

        return ToolTrace(output=output, calls=calls)
