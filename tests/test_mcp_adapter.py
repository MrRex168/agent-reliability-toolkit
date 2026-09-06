from agent_reliability import MCPTraceAdapter, ToolTrace, normalize_mcp_call


def test_normalize_mcp_dict_success():
    call = normalize_mcp_call(
        {"name": "get_order", "arguments": {"order_id": "1234"}, "result": {"status": "shipped"}}
    )
    assert call.name == "get_order"
    assert call.arguments == {"order_id": "1234"}
    assert call.result == {"status": "shipped"}
    assert call.success is True


def test_normalize_mcp_error_marks_call_failed():
    call = normalize_mcp_call(
        {"tool_name": "get_order", "args": {"order_id": "9999"}, "error": "not found"}
    )
    assert call.name == "get_order"
    assert call.success is False
    assert call.result == "not found"


def test_mcp_trace_adapter_normalizes_mapping():
    def runner(prompt):
        return {
            "output": "Order 1234 is shipped.",
            "tool_calls": [
                {"name": "get_order", "arguments": {"order_id": "1234"}, "result": "shipped"}
            ],
        }

    trace = MCPTraceAdapter(runner).run("Where is order 1234?")
    assert isinstance(trace, ToolTrace)
    assert trace.output == "Order 1234 is shipped."
    assert len(trace.calls) == 1
    assert trace.calls[0].name == "get_order"


def test_mcp_trace_adapter_accepts_custom_parsers():
    def runner(prompt):
        return {"answer": "done", "events": [{"name": "save", "arguments": {"id": 1}}]}

    trace = MCPTraceAdapter(
        runner,
        output_parser=lambda raw: raw["answer"],
        calls_parser=lambda raw: raw["events"],
    ).run("save it")
    assert trace.output == "done"
    assert trace.calls[0].name == "save"
    assert trace.calls[0].arguments == {"id": 1}
