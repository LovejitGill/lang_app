"""Small SQLite store for completed tutoring turns, using parameterized SQL."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from errors import StorageError

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "speakwell.sqlite"


def validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("Provide a non-empty session ID.")
    if len(session_id) > 128:
        raise ValueError("Session IDs must be at most 128 characters.")


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create storage if absent; never delete existing history."""
    try:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # A connection's transaction context commits/rolls back; closing closes it.
        with closing(sqlite3.connect(path, timeout=3)) as connection, connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    learner_text TEXT NOT NULL,
                    tutor_reply TEXT NOT NULL,
                    feedback_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS turns_session_id ON turns(session_id, id)"
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    scenario TEXT NOT NULL
                )"""
            )
    except (sqlite3.Error, OSError) as exc:
        raise StorageError(
            "Cannot initialize history. Check the database path and permissions."
        ) from exc


def insert_turn(
    session_id: str,
    learner_text: str,
    tutor_reply: str,
    feedback: list[str],
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Save one complete exchange atomically and return its row ID."""
    validate_session_id(session_id)
    if any(
        not isinstance(s, str) or not s.strip() for s in (learner_text, tutor_reply)
    ):
        raise ValueError("A saved turn needs non-empty learner and tutor text.")
    if not isinstance(feedback, list) or any(not isinstance(s, str) for s in feedback):
        raise ValueError("Feedback must be a list of strings.")
    try:
        with closing(sqlite3.connect(db_path, timeout=3)) as connection, connection:
            cursor = connection.execute(
                """INSERT INTO turns
                (session_id, learner_text, tutor_reply, feedback_json)
                VALUES (?, ?, ?, ?)""",
                (
                    session_id,
                    learner_text,
                    tutor_reply,
                    json.dumps(feedback, ensure_ascii=False),
                ),
            )
            return cursor.lastrowid
    except sqlite3.Error as exc:
        raise StorageError(
            "Could not save history. Check database access or retry after a lock clears."
        ) from exc


def get_history(
    session_id: str, limit: int = 4, db_path: Path = DEFAULT_DB_PATH
) -> list[dict]:
    """Return the latest N complete turns, oldest first, for this session only."""
    validate_session_id(session_id)
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("History limit must be an integer from 1 to 20.")
    try:
        with closing(sqlite3.connect(db_path, timeout=3)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM turns WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        result = []
        for row in reversed(rows):
            turn = dict(row)
            turn["feedback"] = json.loads(turn.pop("feedback_json"))
            result.append(turn)
        return result
    except (sqlite3.Error, json.JSONDecodeError) as exc:
        raise StorageError(
            "Cannot read history. Check the database before continuing this session."
        ) from exc


def create_session(session_id: str, level: str, scenario: str, db_path=DEFAULT_DB_PATH):
    """Persist UI settings so refresh cannot silently change the practice mode."""
    validate_session_id(session_id)
    try:
        with closing(sqlite3.connect(db_path, timeout=3)) as connection, connection:
            connection.execute(
                "INSERT INTO sessions VALUES (?, ?, ?)", (session_id, level, scenario)
            )
    except sqlite3.Error as exc:
        raise StorageError(
            "Cannot start a conversation. Check database access."
        ) from exc


def load_session(session_id: str, db_path=DEFAULT_DB_PATH) -> tuple[dict, list[dict]]:
    """Load UI metadata and its full transcript once on initial page load."""
    validate_session_id(session_id)
    try:
        with closing(sqlite3.connect(db_path, timeout=3)) as connection:
            connection.row_factory = sqlite3.Row
            session = connection.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if session is None:
                raise StorageError("Conversation not found. Start a new conversation.")
            rows = connection.execute(
                "SELECT * FROM turns WHERE session_id = ? ORDER BY id", (session_id,)
            ).fetchall()
        turns = []
        for row in rows:
            turn = dict(row)
            turn["feedback"] = json.loads(turn.pop("feedback_json"))
            turn["saved"] = True
            turns.append(turn)
        return dict(session), turns
    except (sqlite3.Error, json.JSONDecodeError) as exc:
        raise StorageError(
            "Cannot restore the conversation. Check database access."
        ) from exc
