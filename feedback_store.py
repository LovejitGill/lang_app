"""Persist optional grammar jobs against exact saved turns, without changing old rows."""

import json
import sqlite3
import uuid
from contextlib import closing, contextmanager
from time import perf_counter

from errors import StorageError


@contextmanager
def connection(path):
    try:
        with closing(sqlite3.connect(path, timeout=3)) as conn, conn:
            conn.row_factory = sqlite3.Row
            yield conn
    except (sqlite3.Error, OSError, ValueError) as exc:
        raise StorageError(
            "Could not access separate grammar feedback storage."
        ) from exc


def save_reply(session_id, text, reply, reply_seconds, submitted, path):
    """Save reply and pending job atomically, before any grammar inference."""
    job_id = str(uuid.uuid4())
    with connection(path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS grammar_jobs (
            turn_id INTEGER PRIMARY KEY REFERENCES turns(id),
            job_id TEXT NOT NULL UNIQUE,
            state TEXT NOT NULL,
            reply_seconds REAL NOT NULL,
            result_json TEXT
        )""")
        cursor = conn.execute(
            "INSERT INTO turns (session_id, learner_text, tutor_reply, feedback_json) VALUES (?, ?, ?, ?)",
            (session_id, text, reply, "[]"),
        )
        turn_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO grammar_jobs VALUES (?, ?, 'pending', ?, NULL)",
            (turn_id, job_id, reply_seconds),
        )
    return {
        "turn_id": turn_id,
        "job_id": job_id,
        "session_id": session_id,
        "learner_text": text,
        "submitted": submitted,
        "db_path": path,
    }


def claim(job):
    """Only one worker can start this saved job, even after duplicate submissions."""
    with connection(job["db_path"]) as conn:
        cursor = conn.execute(
            """UPDATE grammar_jobs SET state='running'
            WHERE turn_id=? AND job_id=? AND state='pending'
            AND EXISTS (SELECT 1 FROM turns WHERE id=? AND session_id=? AND learner_text=?)""",
            (
                job["turn_id"],
                job["job_id"],
                job["turn_id"],
                job["session_id"],
                job["learner_text"],
            ),
        )
        return cursor.rowcount == 1


def finish(job, result):
    """Match job, turn, session and original text; never attach to the newest turn."""
    with connection(job["db_path"]) as conn:
        cursor = conn.execute(
            """UPDATE grammar_jobs SET state=?, result_json=?
            WHERE turn_id=? AND job_id=? AND state IN ('pending', 'running')
            AND EXISTS (SELECT 1 FROM turns WHERE id=? AND session_id=? AND learner_text=?)""",
            (
                result["state"],
                json.dumps(result, ensure_ascii=False),
                job["turn_id"],
                job["job_id"],
                job["turn_id"],
                job["session_id"],
                job["learner_text"],
            ),
        )
        if cursor.rowcount != 1:
            return False
        if result["state"] == "offered":
            edit = result["edit"]
            feedback = [
                f"{edit['original']} → {edit['replacement']}. {result['explanation']}"
            ]
            conn.execute(
                "UPDATE turns SET feedback_json=? WHERE id=?",
                (json.dumps(feedback, ensure_ascii=False), job["turn_id"]),
            )
        return True


def load(session_id, path):
    with connection(path) as conn:
        if not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='grammar_jobs'"
        ).fetchone():
            return {}
        rows = conn.execute(
            """SELECT g.*, t.session_id, t.learner_text FROM grammar_jobs g
            JOIN turns t ON t.id=g.turn_id WHERE t.session_id=?""",
            (session_id,),
        ).fetchall()
    return {
        row["turn_id"]: {
            **dict(row),
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
        }
        for row in rows
    }


def unavailable(message):
    return {"state": "unavailable", "message": message}


def run_job(job, check):
    if not claim(job):
        return
    try:
        result = check(job["learner_text"])
    except Exception as exc:  # noqa: BLE001 -- worker must not lose the saved reply
        result = {
            **unavailable("Grammar feedback could not finish. Your reply is saved."),
            "diagnostic_type": type(exc).__name__,
        }
    result["total_seconds"] = perf_counter() - job["submitted"]
    finish(job, result)
