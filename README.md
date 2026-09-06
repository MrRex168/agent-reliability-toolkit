# AI Agent Reliability Toolkit

Evaluate whether an AI agent actually works reliably — before putting it into production.

**Open-source, local-first evaluation toolkit for AI agents.** Run the same task repeatedly, measure success and consistency, inspect tool usage, classify failures, evaluate semantic quality, trace executions with OpenTelemetry, store evaluation history, and detect regressions between agent versions.

## 30-second demo

```bash
git clone https://github.com/MrRex168/agent-reliability-toolkit.git
cd agent-reliability-toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e .
agent-reliability eval examples/unreliable_cases.yaml --runs 20
```

The demo agent fails intermittently on purpose. Repeated runs expose failures that a single successful demo would hide.

## Why this exists

An agent can pass a demo and still fail in production. A single successful run tells you almost nothing about reliability.

```text
Test cases → Agent → Repeated runs → Assertions → Failure analysis → Regression check
```

## What it checks

- **Task success** — did the agent satisfy the expected outcome?
- **Consistency** — does it keep passing across repeated runs?
- **Structured output** — required keys and exact JSON objects
- **Text output** — required phrases, regex patterns, and exact values
- **Semantic quality** — optional provider-agnostic LLM-as-a-judge scoring
- **Tool calls** — expected tools, arguments, call order, and failed executions
- **MCP tool traces** — normalize MCP-style calls without forcing an MCP SDK dependency
- **Failure classification** — output, structured-output, tool-selection, tool-argument, tool-execution, and agent errors
- **Latency** — average execution time
- **OpenTelemetry traces** — optional execution spans and evaluation attributes
- **Regression detection** — compare a new evaluation against a baseline
- **Historical storage** — keep evaluation reports locally in SQLite
- **Pass/fail gates** — fail CI when reliability drops beyond an allowed threshold
- **Framework adapters** — LangChain, LangGraph, and generic MCP traces
- **JSON export** — keep results for CI, regression testing, or your own tooling

## Quick start

Requires Python 3.10+.

```bash
agent-reliability eval examples/cases.yaml --runs 10
```

Export a machine-readable report:

```bash
agent-reliability eval examples/cases.yaml --runs 10 --json report.json
```

## Historical evaluation history

v0.8 adds a lightweight SQLite history store. It requires no database server and keeps the toolkit local-first.

Save a report:

```bash
agent-reliability history save report.json --agent my-agent --version 1.2.0
```

List recent evaluations:

```bash
agent-reliability history list
```

Inspect a stored report:

```bash
agent-reliability history show 1
```

Delete an evaluation:

```bash
agent-reliability history delete 1
```

The default database is `.agent-reliability/history.db`. Use `--db path/to/history.db` to choose another location.

The Python API is also available:

```python
from agent_reliability import EvaluationHistory

history = EvaluationHistory("history.db")
evaluation_id = history.save(report, agent="my-agent", version="1.2.0")
records = history.list()
full_report = history.get(evaluation_id)
```

History stores summary metrics plus the original JSON report, providing a clean foundation for future dashboards and historical comparisons.

## LangChain adapter

If your agent or runnable exposes `invoke()`, wrap it without adding LangChain as a dependency of this toolkit.

```python
from agent_reliability import LangChainAdapter, evaluate_cases

agent = LangChainAdapter(my_langchain_agent)
report = evaluate_cases(agent, cases, runs_per_test=20)
```

Use `output_parser` for application-specific results.

## LangGraph adapter

Compiled LangGraph workflows can be evaluated through the same engine.

```python
from agent_reliability import LangGraphAdapter, evaluate_cases

agent = LangGraphAdapter(my_graph)
report = evaluate_cases(agent, cases, runs_per_test=20)
```

For custom graph state:

```python
agent = LangGraphAdapter(
    my_graph,
    input_builder=lambda prompt: {"question": prompt},
    output_parser=lambda state: state["answer"],
)
```

The adapters use a small duck-typed interface, keeping framework dependencies outside the core package.

## MCP tool evaluation

MCP support in v0.6 focuses on one practical problem: MCP clients and agents produce tool-call records, while the reliability engine already knows how to evaluate normalized tool traces.

The toolkit therefore does **not** add an MCP SDK dependency. `MCPTraceAdapter` accepts dictionaries or objects with common MCP-style fields and converts them into the existing `ToolTrace` / `ToolCall` model.

```python
from agent_reliability import MCPTraceAdapter, evaluate_cases


def run_mcp(prompt):
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
report = evaluate_cases(agent, cases, runs_per_test=20)
```

## OpenTelemetry integration

v0.7 adds optional tracing without forcing an observability backend or an OpenTelemetry dependency on every user.

```bash
pip install -e '.[otel]'
```

```python
from agent_reliability import instrument_agent

agent = instrument_agent(my_agent, service_name="my-agent")
result = agent.run("Where is order 1234?")
```

For evaluation-aware instrumentation:

```python
from agent_reliability import record_evaluation, trace_agent_run

with trace_agent_run(tracer, test_id="order-status", run_number=3) as span:
    result = agent.run("Where is order 1234?")
    record_evaluation(span, success=True, failure_count=0, reliability_score=100.0)
```

The toolkit records namespaced `agent_reliability.*` attributes and records exceptions on failed executions. Export traces through the collector or backend your application already uses.

## Regex evaluation

```yaml
expected:
  regex:
    - "order \\d+ is shipped\\.?"
```

Patterns are matched case-insensitively and with multiline support. Invalid patterns are reported as evaluation failures instead of crashing the run.

## LLM-as-a-judge evaluation

The toolkit provides a provider-agnostic judge interface: you bring the model/provider, while the toolkit handles criteria, thresholds, repeated evaluation, and failure reporting.

```python
from agent_reliability import BasicEvaluator, LLMJudgeEvaluator, evaluate_cases

class MyJudge:
    def judge(self, output, input_text, criteria):
        return 0.92, "The response directly answers the question."

evaluator = BasicEvaluator(LLMJudgeEvaluator(MyJudge()))
report = evaluate_cases(agent, cases, runs_per_test=10, evaluator=evaluator)
```

## Regression testing

```bash
agent-reliability eval examples/cases.yaml --runs 20 --json current.json --baseline baseline.json
```

By default, any metric drop is a regression and the command exits with status `1`. Use `--threshold` to allow a small drop.

## Tool-call evaluation

```yaml
expected:
  tool_calls:
    - name: get_order
      arguments:
        order_id: "1234"
  tool_call_mode: exact
```

The evaluator checks expected tool names, argument values, call order, missing calls, and failed executions.

## Failure analysis

Failed runs are classified automatically so you can see *why* an agent failed, not just that it failed.

| Category | Meaning |
|---|---|
| `AGENT_ERROR` | The agent itself raised an exception |
| `OUTPUT_MISMATCH` | Text or exact output did not match |
| `STRUCTURED_OUTPUT_ERROR` | JSON/object structure did not match |
| `TOOL_SELECTION_ERROR` | The wrong or missing tool was selected |
| `TOOL_ARGUMENT_ERROR` | A tool received an unexpected argument value |
| `TOOL_EXECUTION_ERROR` | A tool invocation failed |
| `UNKNOWN` | Failure did not match a known category |

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

### v0.4 ✓
- Regression comparison
- Thresholds and pass/fail gates

### v0.5 ✓
- Regex evaluators
- Provider-agnostic LLM-as-a-judge evaluator
- Semantic evaluation with thresholds

### v0.5.1 ✓
- Dedicated unreliable-agent demo
- 30-second quick-start evaluation
- CI regression quality gate
- LangChain adapter
- LangGraph adapter
- Framework-agnostic adapter design

### v0.6 ✓
- Generic MCP-style tool-call normalization
- MCP trace adapter
- MCP tool name, argument, result, and error normalization
- MCP execution failure detection
- No MCP SDK dependency in core

### v0.7 ✓
- Optional OpenTelemetry tracing
- Agent execution spans
- Evaluation result attributes and events
- Exception recording
- Backend-neutral instrumentation

### v0.8 ✓
- Local SQLite evaluation history
- Save/list/show/delete history commands
- Python history API
- Full report retention
- Agent/version metadata

### Next
- Historical comparison UX
- Web dashboard
- Hosted evaluation platform

## Philosophy

**Build → Test → Observe → Improve → Productize**

The goal is not another observability platform. The goal is a small tool that answers one question quickly:

> **Can I trust this agent to perform this task repeatedly — and did the latest version get better or worse?**

## License

MIT
