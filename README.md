# AI Agent Reliability Toolkit

Evaluate whether an AI agent actually works reliably — before putting it into production.

**Open-source, local-first evaluation toolkit for AI agents.** Run the same task repeatedly, measure success and consistency, and turn failures into a machine-readable reliability report.

## Why this exists

An agent can pass a demo and still fail in production. A single successful run tells you almost nothing about reliability.

```text
Test cases → Agent → Repeated runs → Assertions → Reliability report
```

## What it checks

- **Task success** — did the agent satisfy the expected outcome?
- **Consistency** — does it keep passing across repeated runs?
- **Structured output** — required keys and exact JSON objects
- **Text output** — required phrases and exact values
- **Latency** — average execution time
- **Failures** — agent exceptions and assertion failures
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

## Agent adapter

Your agent only needs a `run(prompt)` method. It can return either text or a Python dictionary/list for structured evaluations.

```python
class MyAgent:
    def run(self, prompt: str):
        return my_agent_framework.invoke(prompt)
```

The CLI loads an adapter with `module:symbol` syntax:

```yaml
agent: my_agent:agent
```

## Example report

```text
AI Agent Reliability Report
───────────────────────────
Tests             2
Runs per test     10
Total runs        20
Successful        18
Failed            2

Task success      90.0%
Consistency       50.0%
Avg latency       0.400s
Reliability       70.0/100

Failures
  refund-policy run 4: missing expected text: '30 days'
  order-status run 7: agent error: TimeoutError: request timed out
```

## Reliability score

The baseline score is intentionally transparent:

- **Task success** = successful runs / total runs
- **Consistency** = test cases with identical pass/fail outcomes across all repeated runs / total test cases
- **Reliability score** = average of task success and consistency

This is an engineering baseline, not a safety certification or guarantee of production readiness.

## Roadmap

### v0.2

- Structured output assertions ✓
- Tool-call correctness
- Failure classification
- Regex evaluators

### v0.3

- LLM-as-a-judge evaluator
- Regression comparison
- GitHub Actions CI evaluation
- Thresholds and pass/fail gates

### Later

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
