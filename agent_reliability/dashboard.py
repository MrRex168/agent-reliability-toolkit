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
.container{max-width:1100px;margin:0 auto;padding:32px 20px}.muted{color:#68737d}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{background:white;border:1px solid #e2e6ea;border-radius:12px;padding:18px;box-shadow:0 1px 2px #00000008}.metric{font-size:28px;font-weight:700;margin-top:6px}.metric-change{margin-top:6px;font-size:13px;font-weight:600;color:#68737d}.table{width:100%;border-collapse:collapse;background:white}.table th,.table td{padding:12px;border-bottom:1px solid #edf0f2;text-align:left}.table th{font-size:13px;color:#68737d;background:#fafbfc}.table tbody tr:last-child td{border-bottom:0}.table a{color:#1769e0;text-decoration:none;font-weight:600}.history-section{background:white;border:1px solid #e2e6ea;border-radius:12px;box-shadow:0 1px 2px #00000008;overflow:hidden}.history-head{padding:18px 18px 14px;border-bottom:1px solid #edf0f2}.history-head h2{margin:0 0 5px}.history-head p{margin:0}.history-table-wrap{overflow-x:auto}.good{font-weight:700}.bad{font-weight:700}.nav{margin-bottom:24px}.nav a{color:#1769e0;text-decoration:none}.chart{background:white;border:1px solid #e2e6ea;border-radius:12px;padding:18px}.chart svg{width:100%;height:280px}.failure{padding:10px 12px;border-left:3px solid #68737d;background:#f8f9fa;margin:7px 0}.failure-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}.failure-stat{background:#f8f9fa;border:1px solid #edf0f2;border-radius:10px;padding:14px}.failure-label{font-size:12px;color:#68737d}.failure-value{margin-top:5px;font-size:18px;font-weight:700;word-break:break-word}.pill{display:inline-block;padding:3px 8px;border-radius:99px;background:#eef1f4;font-size:12px}.status{display:inline-block;padding:3px 8px;border-radius:99px;background:#eef1f4;font-size:12px;font-weight:600}.compare{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.delta{font-weight:700}@media(max-width:800px){.grid,.compare{grid-template-columns:1fr 1fr}.failure-summary{grid-template-columns:1fr}.table{font-size:13px}}
"""

BASE = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Agent Reliability Dashboard</title><style>{{style}}</style></head><body><main class='container'>{{body}}</main></body></html>"""


def _page(body: str) -> str:
    return BASE.replace("{{style}}", STYLE).replace("{{body}}", body)


def _trend_chart(records: list[Any], width: int = 900, height: int = 260) -> str:
    if not records:
        return ""
    ordered = list(reversed(records))
    left, right, top, bottom = 76.0, 28.0, 30.0, 64.0
    plot_width = width - left - right
    plot_height = height - top - bottom
    data_left = left + 28.0
    data_right = width - right - 28.0
    data_width = data_right - data_left
    if len(ordered) == 1:
        x_values = [data_left + data_width / 2]
    else:
        x_values = [data_left + i * data_width / (len(ordered) - 1) for i in range(len(ordered))]

    def y_for(score: float) -> float:
        score = max(0.0, min(100.0, score))
        return top + (100.0 - score) / 100.0 * plot_height

    point_data = [(x, y_for(float(record.reliability_score)), record) for x, record in zip(x_values, ordered)]
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in point_data)
    guides = "".join(
        f"<line x1='{left:.1f}' y1='{y_for(value):.1f}' x2='{width-right:.1f}' y2='{y_for(value):.1f}' stroke='#e2e7ec' stroke-width='1'/>"
        f"<text x='{left-14:.1f}' y='{y_for(value)+4:.1f}' text-anchor='end' font-size='11' fill='#68737d'>{value}</text>"
        for value in (100, 75, 50, 25, 0)
    )
    markers = "".join(
        f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4.5' fill='#17202a'><title>{escape(record.version or f'Evaluation #{record.id}')} — {record.reliability_score:.1f}</title></circle>"
        f"<text x='{x:.1f}' y='{max(y-14, 14):.1f}' text-anchor='middle' font-size='11' font-weight='700' fill='#17202a'>{record.reliability_score:.1f}</text>"
        f"<text x='{x:.1f}' y='{height-34:.1f}' text-anchor='middle' font-size='11' fill='#68737d'>{escape(record.version or f'#{record.id}')}</text>"
        for x, y, record in point_data
    )
    axes = (
        f"<text x='18' y='{top + plot_height / 2:.1f}' text-anchor='middle' font-size='11' font-weight='600' fill='#68737d' transform='rotate(-90 18 {top + plot_height / 2:.1f})'>Reliability score</text>"
        f"<text x='{left + plot_width / 2:.1f}' y='{height-8:.1f}' text-anchor='middle' font-size='11' font-weight='600' fill='#68737d'>Version</text>"
    )
    return (
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Reliability score trend from 0 to 100'>"
        f"<title>Reliability score trend</title>{guides}{axes}"
        f"<polyline fill='none' stroke='#17202a' stroke-width='3' stroke-linejoin='round' stroke-linecap='round' points='{points}'/>"
        f"{markers}</svg>"
    )


def _failure_rows(report: dict[str, Any]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for run in report.get("runs", []):
        for failure in run.get("failure_categories", []):
            if isinstance(failure, dict):
                rows.append((str(failure.get("category", "UNKNOWN")), str(failure.get("severity", "ERROR")), str(failure.get("message", ""))))
    return rows


def _failure_summary(report: dict[str, Any], failed_runs: int) -> str:
    failures = _failure_rows(report)
    counts = Counter(category for category, _, _ in failures)
    if not counts:
        return "<p class='muted'>No classified failure diagnostics in the latest evaluation.</p>"
    primary_category, primary_count = counts.most_common(1)[0]
    return (
        "<div class='failure-summary'>"
        f"<div class='failure-stat'><div class='failure-label'>Primary diagnostic</div><div class='failure-value'>{escape(primary_category)}</div></div>"
        f"<div class='failure-stat'><div class='failure-label'>Diagnostics</div><div class='failure-value'>{len(failures)}</div></div>"
        f"<div class='failure-stat'><div class='failure-label'>Failed runs</div><div class='failure-value'>{failed_runs}</div></div>"
        "</div>"
        f"<p class='muted'>{primary_count} of {len(failures)} diagnostics are {escape(primary_category)}. One failed run can produce multiple assertion-level diagnostics.</p>"
    )


def _history_change(records: list[Any], index: int) -> tuple[str, str]:
    current = records[index]
    previous = next((r for r in records[index + 1:] if r.agent == current.agent), None)
    if previous is None:
        return "Baseline", "—"
    delta = float(current.reliability_score) - float(previous.reliability_score)
    if delta > 0:
        return "Improved", f"+{delta:.1f}"
    if delta < 0:
        return "Lower", f"{delta:.1f}"
    return "Unchanged", "0.0"


def _metric_change(current: float, previous: float | None, suffix: str = "", inverse: bool = False) -> str:
    if previous is None:
        return "Baseline"
    delta = current - previous
    if abs(delta) < 0.05:
        return "No change"
    improved = delta < 0 if inverse else delta > 0
    direction = "▲" if improved else "▼"
    value = abs(delta)
    return f"{direction} {value:.1f}{suffix} vs prior"


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
        row_parts = []
        for index, record in enumerate(records):
            status, delta = _history_change(records, index)
            row_parts.append(
                f"<tr><td><a href='/evaluation/{record.id}'>#{record.id}</a></td>"
                f"<td>{escape(record.version or '—')}</td><td>{escape(record.agent)}</td>"
                f"<td>{record.reliability_score:.1f}</td><td class='delta'>{delta}</td>"
                f"<td>{record.task_success:.1f}%</td><td>{record.failed_runs} / {record.total_runs}</td>"
                f"<td><span class='status'>{status}</span></td></tr>"
            )
        rows = "".join(row_parts)
        if latest:
            previous = next((r for r in records[1:] if r.agent == latest.agent), None)
            reliability_change = _metric_change(latest.reliability_score, previous.reliability_score if previous else None)
            task_success_change = _metric_change(latest.task_success, previous.task_success if previous else None, "%")
            consistency_change = _metric_change(latest.consistency, previous.consistency if previous else None, "%")
            failed_change = _metric_change(float(latest.failed_runs), float(previous.failed_runs) if previous else None, inverse=True)
            cards = (
                "<div class='grid'>"
                f"<div class='card'>Latest reliability<div class='metric'>{latest.reliability_score:.1f}</div><div class='metric-change'>{reliability_change}</div></div>"
                f"<div class='card'>Task success<div class='metric'>{latest.task_success:.1f}%</div><div class='metric-change'>{task_success_change}</div></div>"
                f"<div class='card'>Consistency<div class='metric'>{latest.consistency:.1f}%</div><div class='metric-change'>{consistency_change}</div></div>"
                f"<div class='card'>Failed runs<div class='metric'>{latest.failed_runs} / {latest.total_runs}</div><div class='metric-change'>{failed_change}</div></div>"
                "</div>"
            )
            latest_report = history.get(latest.id)
            failure_analysis = f"<div class='card'><h2>Failure analysis</h2><p class='muted'>Latest evaluation · {escape(latest.agent)}{(' v' + escape(latest.version)) if latest.version else ''}</p>{_failure_summary(latest_report, latest.failed_runs)}</div>"
        else:
            cards = "<div class='card'><h2>No evaluations yet</h2><p class='muted'>Save an evaluation JSON report to start building history.</p><code>agent-reliability history save report.json --agent my-agent --version 1.0.0</code></div>"
            failure_analysis = ""
        chart = f"<div class='chart'><h2>Reliability trend</h2><p class='muted'>Reliability score by saved evaluation (0–100).</p>{_trend_chart(records)}</div>" if records else ""
        table = (
            "<section class='history-section'>"
            "<div class='history-head'><h2>Evaluation history</h2><p class='muted'>Saved evaluations with reliability changes against the prior version of the same agent.</p></div>"
            "<div class='history-table-wrap'>"
            f"<table class='table'><thead><tr><th>Evaluation</th><th>Version</th><th>Agent</th><th>Reliability</th><th>Δ vs prior</th><th>Task success</th><th>Failed runs</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"
            "</div></section>"
        ) if records else ""
        body = f"<div class='nav'><h1>AI Agent Reliability</h1><p class='muted'>Evaluate, track and compare AI agent reliability over time.</p></div>{cards}<br>{chart}<br>{failure_analysis}<br>{table}"
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
