"""SQLite helpers for jobs and OTP state."""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"


def _conn():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                status      TEXT NOT NULL DEFAULT 'pending',
                input_path  TEXT,
                output_path TEXT,
                output_name TEXT,
                row_count   INTEGER,
                processed   INTEGER DEFAULT 0,
                message     TEXT,
                created_at  INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS otps (
                job_id      TEXT PRIMARY KEY,
                otp         TEXT NOT NULL,
                email       TEXT NOT NULL,
                mobile      TEXT NOT NULL,
                attempts    INTEGER NOT NULL DEFAULT 0,
                expires_at  INTEGER NOT NULL
            );
        """)


def create_job(job_id: str, input_path: str, output_path: str,
               output_name: str, row_count: int):
    with _conn() as c:
        c.execute(
            "INSERT INTO jobs (id, status, input_path, output_path, output_name,"
            " row_count, message, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (job_id, "pending", input_path, output_path, output_name,
             row_count, "Queued", int(time.time()))
        )


def update_job(job_id: str, **fields):
    if not fields:
        return
    parts = ", ".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE jobs SET {parts} WHERE id=?",
                  (*fields.values(), job_id))


def get_job(job_id: str):
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def save_otp(job_id: str, otp: str, email: str, mobile: str, ttl: int = 600):
    expires_at = int(time.time()) + ttl
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO otps"
            " (job_id, otp, email, mobile, attempts, expires_at)"
            " VALUES (?,?,?,?,0,?)",
            (job_id, otp, email, mobile, expires_at)
        )


def get_otp(job_id: str):
    with _conn() as c:
        row = c.execute("SELECT * FROM otps WHERE job_id=?",
                        (job_id,)).fetchone()
        return dict(row) if row else None


def increment_otp_attempts(job_id: str):
    with _conn() as c:
        c.execute("UPDATE otps SET attempts=attempts+1 WHERE job_id=?",
                  (job_id,))


def delete_otp(job_id: str):
    with _conn() as c:
        c.execute("DELETE FROM otps WHERE job_id=?", (job_id,))
