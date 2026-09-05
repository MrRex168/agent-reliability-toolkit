# AI Agent Reliability Toolkit

Evaluate whether an AI agent actually works reliably — before putting it into production.

**Open-source, local-first evaluation toolkit for AI agents.** Run the same task repeatedly, measure success and consistency, and turn failures into a machine-readable reliability report.

## Why this exists

An agent can pass a demo and still fail in production.

A single successful run tells you almost nothing about reliability. This toolkit lets you define representative tasks, run an agent repeatedly, evaluate the result, and quantify failure modes.

```text
Test cases → Agent → Repeated runs → Assertions → Reliability report
```

## MVP features

- Python CLI
- YAML test cases
- Any Python agent function through a tiny adapter interface
- Repeat the same test multiple times
- Deterministic assertions for text/JSON outputs
- Task success rate
- Consistency across repeated runs
- Latency measurement
- Failure details per run
- JSON report export
- No hosted service or API key required for the core toolkit

## Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/MrRex168/agent-reliability-toolkit.git
cd agent-reliability-toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the example:

```bash
agent-reliability eval examples/cases.yaml --runs 10
```

Export JSON:

```bash
agent-reliability eval examples/cases.yaml --runs 10 --json report.json
```

## Test case format

```yaml
- id: refund-policy
  input: "What is the refund policy?"
  expected:
    contains:
      - "30 days"
      - "original payment method"

- id: order-status
  input: "Where is order 1234?"
  expected:
    contains:
      - "shipped"
```

The current MVP uses a simple `contains` assertion so evaluations are reproducible and easy to understand. More evaluators can be added without changing the test format.

## Agent adapter

Your agent only needs to implement a function accepting a string and returning a string:

```python
from agent_reliability import Agent

class MyAgent(Agent):
    def run(self, prompt: str) -> str:
        return my_agent_framework.invoke(prompt)
```

For the CLI example, the test file can point at a Python module exposing `agent`:

```yaml
agent: examples.agent:agent
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
Consistency       90.0%
Avg latency       0.4s
Reliability      90/100

Failures
  refund-policy   1/10
  order-status    1/10
```

## Reliability score

The MVP score is intentionally transparent:

- **Task success** = successful runs / total runs
- **Consistency** = tests that produced the same pass/fail outcome on every run, weighted across runs
- **Reliability score** = average of task success and consistency

This is a baseline engineering metric, not a claim that an agent is safe or production-ready. Domain-specific evaluators should be added for high-stakes systems.

## Roadmap

### Next

- Tool-call correctness
- Structured JSON/schema assertions
- Regex and exact-match evaluators
- Retry/failure classification
- LLM-as-a-judge evaluator
- Regression comparison between evaluation runs
- GitHub Actions integration

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
