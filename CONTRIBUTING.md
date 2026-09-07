# Contributing

Thanks for helping improve AI Agent Reliability Toolkit.

## Development setup

Requires Python 3.10+.

```bash
git clone https://github.com/MrRex168/agent-reliability-toolkit.git
cd agent-reliability-toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Run the test suite:

```bash
pytest -q
```

Run the deterministic demo:

```bash
agent-reliability eval examples/unreliable_cases.yaml --runs 20
```

## Pull requests

Please keep changes focused and explain:

1. What problem the change solves.
2. Why the proposed behavior is useful for AI agent developers.
3. How it was tested.
4. Any compatibility or API implications.

For new evaluators or adapters, include deterministic tests and a small example where practical.

## Design principles

- Keep the core package lightweight and dependency-minimal.
- Prefer provider- and framework-agnostic interfaces.
- Keep evaluation results deterministic where possible.
- Make failures actionable rather than merely reporting pass/fail.
- Avoid adding cloud infrastructure to the local-first core without a strong use case.
- Preserve backwards compatibility for public APIs unless a breaking change is explicitly justified.

## Code quality

Before opening a PR, run:

```bash
pytest -q
```

Documentation changes should keep the README quick-start path accurate.
