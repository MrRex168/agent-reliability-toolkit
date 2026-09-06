from __future__ import annotations

from agent_reliability import MCPTraceAdapter


def run_mcp(prompt: str) -> dict:
    """Stand-in for an MCP client/agent execution trace."""
    return {
        "output": "Order 1234 is shipped.",
        "tool_calls": [
            {
                "name": "get_order",
                "arguments": {"order_id": "1234"},
                "result": {"status": "shipped"},
            }
        ],
    }


agent = MCPTraceAdapter(run_mcp)
