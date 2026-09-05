# AI Agent Reliability Toolkit

Evaluate whether an AI agent actually works reliably — before putting it into production.

**Open-source, local-first evaluation toolkit for AI agents.** Run the same task repeatedly, measure success and consistency, inspect tool usage, and turn failures into actionable diagnostics.

## Why this exists

An agent can pass a demo and still fail in production. A single successful run tells you almost nothing about reliability.

```text
Test cases → Agent → Repeated runs → Assertions → Failure analysis → Reliability report
```

## What it checks

- **Task success** — did the agent satisfy the expected outcome?
- **Consistency** — does it keep passing across repeated runs?
- **Structured output** — required keys and exact JSON objects
- **Text output** — required phrases and exact values
- **Tool calls** — expected tools, arguments, call order, and failed executions
- **Failure classification** — output, structured-output, tool-selection, tool-argument, tool-execution, and agent errors
- **Latency** — average execution time
- **JSON export** — keep results for CI, regression testing, or your own tooling

## Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/MrRex168/agent-reliability-toolkit.git
cd agent-reliability-toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e .
agent-reliability eval examples/cases.yaml --runs 10
```

Export a machine-readable report:

```bash
agent-reliability eval examples/cases.yaml --runs 10 --json report.json
```

## Test cases

Text evaluation:

```yaml
agent: examples.agent:agent

cases:
  - id: refund-policy
    input: "What is the refund policy?"
    expected:
      contains:
        - "30 days"
        - "original payment method"
```

Structured-output evaluation:

```yaml
agent: examples.structured_agent:agent

cases:
  - id: order-status
    input: "Where is order 1234?"
    expected:
      required_keys:
        - answer
        - category
      json_equals:
        answer: "Order 1234 is shipped."
        category: "order"
```

Tool-call evaluation:

```yaml
agent: examples.tool_agent:agent

cases:
  - id: order-status
    input: "Where is order 1234?"
    expected:
      contains:
        - "shipped"
      tool_calls:
        - name: get_order
          arguments:
            order_id: "1234"
      tool_call_mode: exact
```

## Agent adapter

Your agent only needs a `run(prompt)` method. It can return text, a Python dictionary/list, or a `ToolTrace` containing the output and recorded tool calls.

```python
class MyAgent:
    def run(self, prompt: str):
        return my_agent_framework.invoke(prompt)
```

For tool evaluation, return a `ToolTrace` with normalized `ToolCall` records. See `examples/tool_agent.py` for a complete example.

The CLI loads an adapter with `module:symbol` syntax:

```yaml
agent: my_agent:agent
```

## Failure analysis

Failed runs are classified automatically so you can see *why* an agent failed, not just that it failed.

```text
Failure Analysis

  order-status — run 3
    [HIGH] TOOL_SELECTION_ERROR: tool call #1: expected 'get_order', got 'search_orders'
    [HIGH] TOOL_ARGUMENT_ERROR: tool call #1 argument 'order_id': expected '1234', got '1243'
```

The taxonomy is intentionally small and deterministic:

| Category | Meaning |
|---|---|
| `AGENT_ERROR` | The agent itself raised an exception |
| `OUTPUT_MISMATCH` | Text or exact output did not match |
| `STRUCTURED_OUTPUT_ERROR` | JSON/object structure did not match |
| `TOOL_SELECTION_ERROR` | The wrong or missing tool was selected |
| `TOOL_ARGUMENT_ERROR` | A tool received an unexpected argument value |
| `TOOL_EXECUTION_ERROR` | A tool invocation failed |
| `UNKNOWN` | Failure did not match a known category |

## Example report

```text
AI Agent Reliability Report
───────────────────────────
Tests             2
Runs per test     10
Total runs        20
Successful        17
Failed            3

Task success      85.0%
Consistency       50.0%
Avg latency       0.400s
Reliability       67.5/100

Failure Analysis

  refund-policy — run 4
    [MEDIUM] OUTPUT_MISMATCH: missing expected text: '30 days'

  order-status — run 7
    [HIGH] AGENT_ERROR: agent error: TimeoutError: request timed out
```

## Reliability score

The baseline score is intentionally transparent:

- **Task success** = successful runs / total runs
- **Consistency** = test cases with identical pass/fail outcomes across all repeated runs / total test cases
- **Reliability score** = average of task success and consistency

This is an engineering baseline, not a safety certification or guarantee of production readiness.

## Roadmap

### v0.3 ✓

- Structured output assertions
- Tool-call correctness
- Failure classification

### v0.4 — next

- Regex evaluators
- LLM-as-a-judge evaluator
- Regression comparison
- Thresholds and pass/fail gates

### Later

- GitHub Actions CI evaluation
- LangGraph/LangChain adapters
- MCP tool evaluation
- OpenTelemetry integration
- Web dashboard
- Historical evaluation database
- Hosted evaluation platform

## Philosophy

**Build → Test → Observe → Improve → Productize**

The goal is not another observability platform. The goal is a small tool that answers one question quickly:

> **Can I trust this agent to perform this task repeatedly?**

## License

MIT
