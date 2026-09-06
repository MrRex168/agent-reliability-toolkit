# AI Agent Reliability Toolkit

Evaluate whether an AI agent actually works reliably — before putting it into production.

**Open-source, local-first evaluation toolkit for AI agents.** Run the same task repeatedly, measure success and consistency, inspect tool usage, classify failures, evaluate semantic quality, and detect regressions between agent versions.

## 30-second demo

Clone the repo, install it, and run the intentionally unreliable demo agent:

```bash
git clone https://github.com/MrRex168/agent-reliability-toolkit.git
cd agent-reliability-toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e .
agent-reliability eval examples/unreliable_cases.yaml --runs 20
```

The demo agent fails intermittently on purpose. Repeated runs expose failures that a single successful demo would hide.

Example:

```text
AI Agent Reliability Report
───────────────────────────
Tests             2
Runs per test     20
Total runs        40
Successful        34
Failed            6

Task success      85.0%
Consistency       0.0%
Reliability       42.5/100

Failure Analysis
  refund-policy — run 5
    [HIGH] OUTPUT_MISMATCH: missing expected text: '30 days'
```

Your own agent needs only a `run(prompt)` method. The toolkit does not require a specific agent framework or LLM provider.

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
- **Semantic quality** — optional LLM-as-a-judge scoring against explicit criteria
- **Tool calls** — expected tools, arguments, call order, and failed executions
- **Failure classification** — output, structured-output, tool-selection, tool-argument, tool-execution, and agent errors
- **Latency** — average execution time
- **Regression detection** — compare a new evaluation against a baseline
- **Pass/fail gates** — fail CI or scripts when reliability drops beyond an allowed threshold
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

## Regex evaluation

Use regex when an exact string is too strict but the output still needs to follow a predictable pattern:

```yaml
expected:
  regex:
    - "order \\d+ is shipped\\.?"
```

Patterns are matched case-insensitively and with multiline support. Invalid patterns are reported as evaluation failures instead of crashing the run.

## LLM-as-a-judge evaluation

Deterministic assertions are excellent for structure and exact behavior, but many agent tasks are semantic. The toolkit provides a provider-agnostic judge interface: you bring the model/provider, while the toolkit handles criteria, thresholds, repeated evaluation, and failure reporting.

```python
from agent_reliability import BasicEvaluator, LLMJudgeEvaluator, evaluate_cases

class MyJudge:
    def judge(self, output, input_text, criteria):
        # Call your preferred LLM provider here.
        return 0.92, "The response directly answers the question."

evaluator = BasicEvaluator(LLMJudgeEvaluator(MyJudge()))
report = evaluate_cases(agent, cases, runs_per_test=10, evaluator=evaluator)
```

The test case stays provider-neutral:

```yaml
expected:
  judge:
    criteria:
      - "The response directly answers the user's question."
      - "The response does not invent unsupported facts."
    threshold: 0.80
```

The judge returns a score from `0.0` to `1.0`. A score below the configured threshold fails the run. No API key or LLM dependency is required by the core package, which keeps local tests and CI deterministic unless you explicitly supply a live judge.

## Regression testing

Save a known-good evaluation as a baseline, then compare future agent versions against it:

```bash
agent-reliability eval examples/cases.yaml --runs 20 --json current.json --baseline baseline.json
```

The command checks overall task success, consistency, reliability score, and per-test success rates. By default, **any drop is a regression** and the command exits with status `1`.

Allow a small measurement change with `--threshold`:

```bash
agent-reliability eval examples/cases.yaml --runs 20 --baseline baseline.json --threshold 2
```

This makes the toolkit usable as a lightweight quality gate before shipping an agent change.

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

### v0.5.1

- Dedicated unreliable-agent demo
- 30-second quick-start evaluation
- CI regression quality gate
- Improved developer experience and examples

### Next

- LangGraph/LangChain adapters
- MCP tool evaluation
- OpenTelemetry integration
- Web dashboard
- Historical evaluation database
- Hosted evaluation platform

## Philosophy

**Build → Test → Observe → Improve → Productize**

The goal is not another observability platform. The goal is a small tool that answers one question quickly:

> **Can I trust this agent to perform this task repeatedly — and did the latest version get better or worse?**

## License

MIT
