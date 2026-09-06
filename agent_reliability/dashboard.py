from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path
from typing import Any

from .history import EvaluationHistory
from .regression import compare_reports


def _flask():
    try:
        from flask import Flask, abort, jsonify, render_template_string
    except ImportError as exc:
        raise RuntimeError(
            "Dashboard dependencies are optional. Install with "
            "pip install -e '.[dashboard]'"
        ) from exc
    return Flask, abort, jsonify, render_template_string


STYLE = """
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;background:#f6f7f9;color:#17202a}
.container{max-width:1100px;margin:0 auto;padding:32px 20px}.muted{color:#68737d}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{background:white;border:1px solid #e2e6ea;border-radius:12px;padding:18px;box-shadow:0 1px 2px #00000008}.metric{font-size:28px;font-weight:700;margin-top:6px}.table{width:100%;border-collapse:collapse;background:white;border:1px solid #e2e6ea;border-radius:12px;overflow:hidden}.table th,.table td{padding:12px;border-bottom:1px solid #edf0f2;text-align:left}.table th{font-size:13px;color:#68737d}.good{font-weight:700}.bad{font-weight:700}.nav{margin-bottom:24px}.nav a{color:#1769e0;text-decoration:none}.chart{background:white;border:1px solid #e2e6ea;border-radius:12px;padding:18px}.chart svg{width:100%;height:190px}.failure{padding:10px 12px;border-left:3px solid #68737d;background:#f8f9fa;margin:7px 0}.pill{display:inline-block;padding:3px 8px;border-radius:99px;background:#eef1f4;font-size:12px}.compare{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.delta{font-weight:700}@media(max-width:800px){.grid,.compare{grid-template-columns:1fr 1fr}.table{font-size:13px}}
"""

BASE = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Agent Reliability Dashboard</title><style>{{style}}</style></head><body><main class='container'>{{body}}</main></body></html>"""


def _page(body: str) -> str:
    return BASE.replace("{{style}}", STYLE).replace("{{body}}", body)


def _svg_points(records: list[Any], width: int = 900, height: int = 170) -> str:
    if not records:
        return ""
    values = [float(r.reliability_score) for r in reversed(records)]
    if len(values) == 1:
        x_values = [width / 2]
    else:
        x_values = [i * width / (len(values) - 1) for i in range(len(values))]
    low, high = min(values), max(values)
    span = max(high - low, 1.0)
    y_values = [height - ((v - low) / span) * (height - 20) - 10 for v in values]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(x_values, y_values))


def _failure_rows(report: dict[str, Any]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for run in report.get("runs", []):
        for failure in run.get("failure_categories", []):
            if isinstance(failure, dict):
                rows.append((str(failure.get("category", "UNKNOWN")), str(failure.get("severity", "ERROR")), str(failure.get("message", ""))))
    return rows


def _record(history: EvaluationHistory, evaluation_id: int):
    for record in history.list(limit=1000):
        if record.id == evaluation_id:
            return record
    return None


def create_app(db_path: str | Path = ".agent-reliability/history.db"):
    Flask, abort, jsonify, render_template_string = _flask()
    app = Flask(__name__)
    history = EvaluationHistory(db_path)

    @app.get("/")
    def index():
        records = history.list(limit=50)
        latest = records[0] if records else None
        points = _svg_points(records)
        rows = "".join(
            f"<tr><td><a href='/evaluation/{r.id}'>#{r.id}</a></td><td>{escape(r.created_at)}</td>"
            f"<td>{escape(r.agent)}{(' v' + escape(r.version)) if r.version else ''}</td>"
            f"<td>{r.reliability_score:.1f}</td><td>{r.task_success:.1f}%</td>"
            f"<td>{r.consistency:.1f}%</td><td>{r.failed_runs}</td></tr>" for r in records
        )
        if latest:
            cards = f"<div class='grid'><div class='card'>Latest reliability<div class='metric'>{latest.reliability_score:.1f}</div></div><div class='card'>Task success<div class='metric'>{latest.task_success:.1f}%</div></div><div class='card'>Consistency<div class='metric'>{latest.consistency:.1f}%</div></div><div class='card'>Evaluations<div class='metric'>{len(records)}</div></div></div>"
        else:
            cards = "<div class='card'><h2>No evaluations yet</h2><p class='muted'>Save an evaluation JSON report to start building history.</p><code>agent-reliability history save report.json --agent my-agent --version 1.0.0</code></div>"
        chart = f"<div class='chart'><h2>Reliability trend</h2><svg viewBox='0 0 900 170' preserveAspectRatio='none'><polyline fill='none' stroke='currentColor' stroke-width='3' points='{points}'/></svg></div>" if records else ""
        table = f"<table class='table'><thead><tr><th>ID</th><th>Date</th><th>Agent</th><th>Reliability</th><th>Task success</th><th>Consistency</th><th>Failed</th></tr></thead><tbody>{rows}</tbody></table>" if records else ""
        body = f"<div class='nav'><h1>AI Agent Reliability</h1><p class='muted'>Evaluate, track and compare AI agent reliability over time.</p></div>{cards}<br>{chart}<br>{table}"
        return render_template_string(_page(body))

    @app.get("/evaluation/<int:evaluation_id>")
    def evaluation(evaluation_id: int):
        record = _record(history, evaluation_id)
        if record is None:
            abort(404)
        report = history.get(evaluation_id)
        failures = _failure_rows(report)
        failure_counts = Counter(category for category, _, _ in failures)
        failure_html = "".join(f"<div class='failure'><span class='pill'>{escape(category)}</span> {escape(message)}</div>" for category, _, message in failures) or "<p class='muted'>No classified failures.</p>"
        run_rows = "".join(f"<tr><td>{escape(str(r.get('test_id','')))}</td><td>{r.get('run_number','')}</td><td>{'PASS' if r.get('success') else 'FAIL'}</td><td>{float(r.get('latency_seconds',0)):.3f}s</td><td>{escape(str(r.get('output','')))}</td></tr>" for r in report.get('runs', []))
        breakdown = ", ".join(f"{escape(k)}: {v}" for k, v in failure_counts.most_common()) or "None"
        body = f"<div class='nav'><a href='/'>← Dashboard</a><h1>Evaluation #{record.id}</h1><p class='muted'>{escape(record.agent)}{(' v' + escape(record.version)) if record.version else ''} · {escape(record.created_at)}</p></div><div class='grid'><div class='card'>Reliability<div class='metric'>{record.reliability_score:.1f}</div></div><div class='card'>Task success<div class='metric'>{record.task_success:.1f}%</div></div><div class='card'>Consistency<div class='metric'>{record.consistency:.1f}%</div></div><div class='card'>Failed runs<div class='metric'>{record.failed_runs}</div></div></div><br><div class='card'><h2>Failure breakdown</h2><p>{breakdown}</p>{failure_html}</div><br><table class='table'><thead><tr><th>Test</th><th>Run</th><th>Status</th><th>Latency</th><th>Output</th></tr></thead><tbody>{run_rows}</tbody></table>"
        return render_template_string(_page(body))

    @app.get("/compare/<int:baseline_id>/<int:current_id>")
    def compare(baseline_id: int, current_id: int):
        baseline_record = _record(history, baseline_id)
        current_record = _record(history, current_id)
        if baseline_record is None or current_record is None:
            abort(404)
        result = compare_reports(history.get(baseline_id), history.get(current_id))
        changes = "".join(f"<tr><td>{escape(c.metric)}</td><td>{c.baseline:.1f}</td><td>{c.current:.1f}</td><td class='delta'>{c.delta:+.1f}</td><td>{'REGRESSION' if c.regressed else 'OK'}</td></tr>" for c in result.changes)
        status = "PASS" if result.passed else "REGRESSION DETECTED"
        body = f"<div class='nav'><a href='/'>← Dashboard</a><h1>Evaluation comparison</h1><p class='muted'>#{baseline_id} → #{current_id}</p></div><div class='card'><h2>{status}</h2><p>Allowed metric drop: {result.threshold:.1f}</p></div><br><table class='table'><thead><tr><th>Metric</th><th>Baseline</th><th>Current</th><th>Delta</th><th>Status</th></tr></thead><tbody>{changes}</tbody></table>"
        return render_template_string(_page(body))

    @app.get("/api/evaluations")
    def api_evaluations():
        return jsonify([r.__dict__ for r in history.list(limit=100)])

    @app.get("/api/evaluations/<int:evaluation_id>")
    def api_evaluation(evaluation_id: int):
        try:
            return jsonify(history.get(evaluation_id))
        except KeyError:
            abort(404)

    return app


def run_dashboard(db_path: str | Path = ".agent-reliability/history.db", host: str = "127.0.0.1", port: int = 5000) -> None:
    app = create_app(db_path)
    app.run(host=host, port=port, debug=False)


__all__ = ["create_app", "run_dashboard"]
