# AI Agent Reliability Toolkit

**Evaluate whether an AI agent actually works reliably — before putting it into production.**

Open-source, local-first tooling for repeatedly testing agents, measuring reliability, inspecting tool usage, classifying failures, evaluating semantic quality, tracing executions, storing evaluation history, and catching regressions between versions.

[![Tests](https://github.com/MrRex168/agent-reliability-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/MrRex168/agent-reliability-toolkit/actions/workflows/test.yml)

## Why this exists

A successful demo does not prove an agent is reliable.

Agents can fail intermittently, choose the wrong tool, send incorrect arguments, return malformed output, or get worse after a code/model change. This toolkit makes those failures measurable and repeatable.

```text
Test cases → Agent → Repeated runs → Assertions → Failure analysis → Regression gate
```

## 30-second demo

Requires Python 3.10+.

```bash
git clone https://github.com/MrRex168/agent-reliability-toolkit.git
cd agent-reliability-toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e .
agent-reliability eval examples/unreliable_cases.yaml --runs 20
```

The included demo agent is intentionally unreliable: some requests fail intermittently. Repeated evaluation exposes failures that a single successful demo would hide.

You should see a report containing task success, consistency, latency, reliability, and categorized failures.

### See the dashboard

Install the optional dashboard dependency:

```bash
pip install -e '.[dashboard]'
agent-reliability dashboard
```

The local dashboard shows evaluation history, reliability trends, individual runs, failure categories, and baseline/current comparisons.

## What it checks

- **Task success** — did the agent satisfy the expected outcome?
- **Consistency** — does it keep passing across repeated runs?
- **Text output** — required phrases, regex patterns, and exact values
- **Structured output** — required keys and exact JSON/object values
- **Semantic quality** — provider-agnostic LLM-as-a-judge scoring
- **Tool calls** — expected tools, arguments, call order, and failed executions
- **MCP traces** — normalize MCP-style calls without forcing an MCP SDK dependency
- **Failure classification** — actionable categories for output, tools, and agent errors
- **Latency** — average execution time
- **OpenTelemetry** — optional execution spans and evaluation attributes
- **Regression detection** — compare a new evaluation against a baseline
- **Evaluation history** — local SQLite storage with agent/version metadata
- **CI quality gates** — fail CI when reliability drops beyond an allowed threshold
- **Framework adapters** — LangChain, LangGraph, and generic MCP traces
- **JSON export** — machine-readable reports for CI and custom tooling

## Quick start

Create an evaluation YAML file:

```yaml
agent: examples.agent:agent
cases:
  - id: greeting
    input: "Say hello"
    expected:
      contains: ["hello"]
```

Run it repeatedly:

```bash
agent-reliability eval cases.yaml --runs 10
```

Export a report:

```bash
agent-reliability eval cases.yaml --runs 10 --json report.json
```

## Regression testing

Compare a new evaluation with a known-good JSON baseline:

```bash
agent-reliability eval cases.yaml \
  --runs 20 \
  --json current.json \
  --baseline baseline.json
```

By default, any metric drop is treated as a regression and the command exits with status `1`. Use `--threshold` when a small metric drop is acceptable.

This makes the toolkit useful as a lightweight CI quality gate for agent changes.

## Evaluation history

Store reports locally in SQLite. No database server is required.

```bash
agent-reliability history save report.json --agent my-agent --version 1.2.0
agent-reliability history list
agent-reliability history show 1
agent-reliability history compare 1 2
agent-reliability history delete 1
```

Default database: `.agent-reliability/history.db`.

Python API:

```python
from agent_reliability import EvaluationHistory

history = EvaluationHistory("history.db")
evaluation_id = history.save(report, agent="my-agent", version="1.2.0")
records = history.list()
full_report = history.get(evaluation_id)
```

## Framework adapters

### LangChain

If your agent or runnable exposes `invoke()`, wrap it without making LangChain a dependency of the toolkit:

```python
from agent_reliability import LangChainAdapter, evaluate_cases

agent = LangChainAdapter(my_langchain_agent)
report = evaluate_cases(agent, cases, runs_per_test=20)
```

### LangGraph

Compiled LangGraph workflows can use the same evaluation engine:

```python
from agent_reliability import LangGraphAdapter, evaluate_cases

agent = LangGraphAdapter(my_graph)
report = evaluate_cases(agent, cases, runs_per_test=20)
```

For custom graph state, provide `input_builder` and `output_parser`.

### MCP

`MCPTraceAdapter` converts common MCP-style tool-call records into the toolkit's normalized `ToolTrace` / `ToolCall` model. The core package does not require an MCP SDK.

```python
from agent_reliability import MCPTraceAdapter, evaluate_cases

agent = MCPTraceAdapter(run_mcp)
report = evaluate_cases(agent, cases, runs_per_test=20)
```

## Tool-call evaluation

Define expected calls in YAML:

```yaml
expected:
  tool_calls:
    - name: get_order
      arguments:
        order_id: "1234"
  tool_call_mode: exact
```

The evaluator can detect wrong tools, missing calls, unexpected arguments, call-order problems, and failed tool executions.

## Regex evaluation

```yaml
expected:
  regex:
    - "order \\d+ is shipped\\.?"
```

Patterns are matched case-insensitively with multiline support. Invalid patterns become evaluation failures rather than crashing the run.

## LLM-as-a-judge

Bring your own model/provider. The toolkit handles criteria, thresholds, repeated evaluation, and failure reporting without hard-coding an LLM vendor.

```python
from agent_reliability import BasicEvaluator, LLMJudgeEvaluator, evaluate_cases

class MyJudge:
    def judge(self, output, input_text, criteria):
        return 0.92, "The response directly answers the question."

evaluator = BasicEvaluator(LLMJudgeEvaluator(MyJudge()))
report = evaluate_cases(agent, cases, runs_per_test=10, evaluator=evaluator)
```

## OpenTelemetry

Install the optional integration:

```bash
pip install -e '.[otel]'
```

```python
from agent_reliability import instrument_agent

agent = instrument_agent(my_agent, service_name="my-agent")
result = agent.run("Where is order 1234?")
```

The toolkit stays backend-neutral and records namespaced `agent_reliability.*` attributes. Use your existing OpenTelemetry collector/backend for export.

## Failure analysis

Failures are classified automatically so you can see *why* an agent failed, not only that it failed.

| Category | Meaning |
|---|---|
| `AGENT_ERROR` | The agent raised an exception |
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

## Architecture

```text
                 ┌──────────────────┐
                 │    Your Agent    │
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │ Framework / MCP  │
                 │    Adapters      │
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │ Repeated Tests   │
                 │ + Evaluators     │
                 └────────┬─────────┘
                          │
              ┌───────────▼───────────┐
              │ Failure Classification │
              └───────────┬───────────┘
                          │
          ┌───────────────▼────────────────┐
          │ Reports / History / Dashboard │
          └───────────────┬────────────────┘
                          │
                 ┌────────▼─────────┐
                 │ Regression Gate  │
                 └──────────────────┘
```

## Design principles

- **Local-first** — no cloud account required.
- **Dependency-minimal** — integrations are optional.
- **Provider-agnostic** — bring your own LLM, framework, and observability backend.
- **Actionable failures** — explain what went wrong.
- **Repeatability** — reliability requires repeated execution, not one demo run.
- **CI-friendly** — JSON reports and non-zero regression exits fit existing pipelines.

## Roadmap

### v1.0 ✓ — Open Source Launch Release

- Repeated agent evaluation
- Structured, regex, semantic, and tool-call evaluation
- MCP trace support
- Failure classification
- Regression testing and CI gates
- OpenTelemetry integration
- SQLite evaluation history
- Historical comparison
- Local web dashboard
- LangChain and LangGraph adapters
- Deterministic unreliable-agent demo
- Developer documentation and contribution workflow

### Next — Validation

- Gather developer feedback and real-world evaluation cases
- Measure GitHub stars, installs, forks, and repeat usage
- Identify the most valuable workflows
- Prioritize the smallest high-demand hosted feature

### Future — Hosted platform

- Hosted evaluation workspace
- Team/project management
- Cloud evaluation history
- Automated agent monitoring
- Usage-based and team plans

The hosted roadmap will be driven by open-source usage rather than built speculatively.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and design guidelines.

Bug reports and feature requests can be submitted through the GitHub issue templates.

## License

MIT License. See `LICENSE`.
