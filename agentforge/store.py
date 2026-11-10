"""Penyimpanan riwayat run ke SQLite.

Skema dibaca dari schema.sql di root project agar skema yang sama
persis dipakai oleh aplikasi, skrip seed, dan tes.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import PROJECT_ROOT

SCHEMA_PATH = PROJECT_ROOT / "schema.sql"


def init_db(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        conn.executescript(fh.read())
    conn.commit()
    return conn


def save_run(conn: sqlite3.Connection, result: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO runs
        (run_id, workflow, title, status, mode, reviewer_score,
         revision_rounds, total_tokens, total_cost_usd, final_output)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["run_id"],
            result["workflow"],
            result["title"],
            result["status"],
            result["mode"],
            result["reviewer_score"],
            result["revision_rounds"],
            result["total_tokens"],
            result["total_cost_usd"],
            result["final_output"],
        ),
    )
    conn.execute("DELETE FROM run_steps WHERE run_id = ?", (result["run_id"],))
    for step in result["steps"]:
        conn.execute(
            """
            INSERT INTO run_steps
            (run_id, step_id, agent, action, model, mode, prompt_tokens,
             completion_tokens, cost_usd, status, attempts, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["run_id"],
                step["step_id"],
                step["agent"],
                step["action"],
                step["model"],
                step["mode"],
                step["prompt_tokens"],
                step["completion_tokens"],
                step["cost_usd"],
                step["status"],
                step["attempts"],
                step["duration_ms"],
            ),
        )
    conn.commit()


def list_runs(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM runs ORDER BY created_at, run_id").fetchall()
    return [dict(r) for r in rows]


def list_steps(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM run_steps WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
    return [dict(r) for r in rows]
