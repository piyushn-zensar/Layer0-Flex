"""
Minimal persistence layer for pipeline runs.

A "run" pauses after every stage to wait for human approval — that
pause has to survive between separate HTTP requests (submit RFP now,
approve Stage 1 five minutes later from a different browser tab), so
state cannot just live in memory. SQLite with a single JSON blob column
is the simplest thing that is actually correct for this; it avoids
requiring a separate database server for a system meant to be simple
to install and run locally.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone

from config import settings


def _connect():
    conn = sqlite3.connect(settings.STATE_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_run(rfp_text: str) -> str:
    run_id = str(uuid.uuid4())
    data = {
        "run_id": run_id,
        "rfp_text": rfp_text,
        "status": "created",       # created | awaiting_approval | completed | rejected | error
        "current_stage": 0,
        "stage_outputs": {},        # {"1": {...}, "2": {...}, ...}
        "approvals": {},            # {"1": {"approved": true, "approver": "...", "timestamp": "..."}}
    }
    now = _now()
    conn = _connect()
    conn.execute(
        "INSERT INTO pipeline_runs (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (run_id, json.dumps(data), now, now),
    )
    conn.commit()
    conn.close()
    return run_id


def get_run(run_id: str) -> dict:
    conn = _connect()
    row = conn.execute("SELECT data FROM pipeline_runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    if row is None:
        raise KeyError(f"No pipeline run found with id {run_id}")
    return json.loads(row[0])


def save_run(run_id: str, data: dict):
    conn = _connect()
    conn.execute(
        "UPDATE pipeline_runs SET data = ?, updated_at = ? WHERE id = ?",
        (json.dumps(data), _now(), run_id),
    )
    conn.commit()
    conn.close()


def list_runs() -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, data, created_at, updated_at FROM pipeline_runs ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    out = []
    for run_id, data, created_at, updated_at in rows:
        d = json.loads(data)
        out.append({
            "run_id": run_id, "status": d["status"], "current_stage": d["current_stage"],
            "created_at": created_at, "updated_at": updated_at,
        })
    return out
