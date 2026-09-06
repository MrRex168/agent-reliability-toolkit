# Local Web Dashboard

v0.9 adds a lightweight local dashboard on top of the existing SQLite evaluation history.

## Install

```bash
pip install -e '.[dashboard]'
```

## Launch

```bash
agent-reliability dashboard
```

By default it binds to `127.0.0.1:5000` and reads `.agent-reliability/history.db`.

Use another database, host, or port when needed:

```bash
agent-reliability dashboard --db path/to/history.db --host 127.0.0.1 --port 5000
```

## What it provides

- Latest reliability, task-success, consistency, and evaluation counts
- Reliability trend across recent evaluations
- Evaluation history with agent/version metadata
- Run-level results and outputs
- Failure-category breakdown
- Baseline vs current evaluation comparison
- JSON API endpoints for simple integrations

Endpoints:

- `/` — dashboard
- `/evaluation/<id>` — evaluation details
- `/compare/<baseline_id>/<current_id>` — regression comparison
- `/api/evaluations` — historical evaluation summaries
- `/api/evaluations/<id>` — full stored report

The dashboard is intentionally local-first. It adds no authentication, hosted infrastructure, frontend framework, or external chart dependency. The same SQLite database used by the CLI is the source of truth.

## Workflow

```text
Agent → Evaluation → SQLite History → Dashboard → Compare → Improve
```
