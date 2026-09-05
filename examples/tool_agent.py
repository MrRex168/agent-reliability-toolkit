from __future__ import annotations

from agent_reliability.tools import ToolRecorder, ToolTrace


def get_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "shipped"}


def agent(prompt: str) -> ToolTrace:
    recorder = ToolRecorder({"get_order": get_order})
    # A tiny deterministic example of an agent deciding to use a tool.
    order_id = "1234"
    result = recorder.call("get_order", order_id=order_id)
    return ToolTrace(output=f"Order {order_id} is {result['status']}.", calls=recorder.calls)
