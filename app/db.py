import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect():
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT,
                topic TEXT,
                mode TEXT,
                competitor_url TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                result_json TEXT
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                status TEXT,
                stage TEXT,
                error TEXT,
                created_at TEXT,
                updated_at TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                message TEXT NOT NULL DEFAULT ''
            );
            """
        )
        existing = {row["name"] for row in connection.execute("PRAGMA table_info(jobs)")}
        if "progress" not in existing:
            connection.execute("ALTER TABLE jobs ADD COLUMN progress INTEGER NOT NULL DEFAULT 0")
        if "message" not in existing:
            connection.execute("ALTER TABLE jobs ADD COLUMN message TEXT NOT NULL DEFAULT ''")


def create_project(data: dict) -> None:
    with connect() as connection:
        connection.execute(
            """INSERT INTO projects
               (id, title, topic, mode, competitor_url, status, created_at, updated_at, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                data["id"], data["title"], data["topic"], data["mode"],
                data.get("competitor_url"), "queued", now(), now(),
            ),
        )


def create_job(job_id: str, project_id: str) -> None:
    with connect() as connection:
        connection.execute(
            """INSERT INTO jobs
               (id, project_id, status, stage, error, created_at, updated_at, progress, message)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
            (job_id, project_id, "queued", "queued", None, now(), now(), "Waiting to start"),
        )


def update_job(
    job_id: str,
    status: str,
    stage: str,
    error: str | None = None,
    progress: int | None = None,
    message: str | None = None,
) -> None:
    fields = ["status = ?", "stage = ?", "error = ?", "updated_at = ?"]
    values: list = [status, stage, error, now()]
    if progress is not None:
        fields.append("progress = ?")
        values.append(max(0, min(100, int(progress))))
    if message is not None:
        fields.append("message = ?")
        values.append(message[:500])
    values.append(job_id)
    with connect() as connection:
        connection.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", values)


def update_project_status(project_id: str, status: str) -> None:
    with connect() as connection:
        connection.execute(
            "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
            (status, now(), project_id),
        )


def save_result(project_id: str, result: dict) -> None:
    with connect() as connection:
        connection.execute(
            "UPDATE projects SET result_json = ?, status = 'completed', updated_at = ? WHERE id = ?",
            (json.dumps(result, ensure_ascii=False), now(), project_id),
        )


def _project_dict(row) -> dict:
    data = dict(row)
    if data.get("result_json"):
        data["result"] = json.loads(data.pop("result_json"))
    else:
        data.pop("result_json", None)
    return data


def get_project(project_id: str) -> dict | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return _project_dict(row) if row else None


def list_projects(limit: int = 25, offset: int = 0) -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM projects ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (max(1, min(100, limit)), max(0, offset)),
        ).fetchall()
    return [_project_dict(row) for row in rows]


def get_job(job_id: str) -> dict | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None
