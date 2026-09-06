from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvaluationRecord:
    id: int
    created_at: str
    agent: str
    version: str | None
    task_success: float
    consistency: float
    reliability_score: float
    total_runs: int
    failed_runs: int


class EvaluationHistory:
    """Small SQLite-backed store for evaluation history."""

    def __init__(self, path: str | Path = ".agent-reliability/history.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    agent TEXT NOT NULL,
                    version TEXT,
                    task_success REAL NOT NULL,
                    consistency REAL NOT NULL,
                    reliability_score REAL NOT NULL,
                    total_runs INTEGER NOT NULL,
                    failed_runs INTEGER NOT NULL,
                    report_json TEXT NOT NULL
                )"""
            )

    def save(self, report: dict[str, Any], *, agent: str = "unknown", version: str | None = None) -> int:
        runs = report.get("runs", [])
        total_runs = len(runs)
        failed_runs = sum(1 for run in runs if not run.get("success"))
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO evaluations
                (agent, version, task_success, consistency, reliability_score,
                 total_runs, failed_runs, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    agent,
                    version,
                    float(report.get("task_success", 0.0)),
                    float(report.get("consistency", 0.0)),
                    float(report.get("reliability_score", 0.0)),
                    total_runs,
                    failed_runs,
                    json.dumps(report, sort_keys=True),
                ),
            )
            return int(cursor.lastrowid)

    def list(self, limit: int = 20) -> list[EvaluationRecord]:
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, created_at, agent, version, task_success,
                          consistency, reliability_score, total_runs, failed_runs
                   FROM evaluations ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [EvaluationRecord(*row) for row in rows]

    def get(self, evaluation_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT report_json FROM evaluations WHERE id = ?", (evaluation_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"evaluation not found: {evaluation_id}")
        return json.loads(row[0])

    def delete(self, evaluation_id: int) -> None:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
            if cursor.rowcount == 0:
                raise KeyError(f"evaluation not found: {evaluation_id}")


__all__ = ["EvaluationHistory", "EvaluationRecord"]
