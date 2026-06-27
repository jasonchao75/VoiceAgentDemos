import sqlite3
import os
import json
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).parent / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "transcriptions.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            language TEXT,
            final_transcript TEXT,
            audio_file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dictionary_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            hotwords TEXT,
            replacements TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_name TEXT,
            language TEXT,
            profile_id INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            file_path TEXT,
            status TEXT,
            final_transcript TEXT,
            error_message TEXT,
            ground_truth TEXT,
            wer REAL,
            wer_errors INTEGER,
            wer_words INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY(run_id) REFERENCES benchmark_runs(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_ground_truths (
            file_path TEXT PRIMARY KEY,
            ground_truth TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_transcription(
    session_id: str, language: str, final_transcript: str, audio_file_path: str
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO transcriptions (session_id, language, final_transcript, audio_file_path)
        VALUES (?, ?, ?, ?)
    """,
        (session_id, language, final_transcript, audio_file_path),
    )
    conn.commit()
    conn.close()


def create_benchmark_run(run_name: str, language: str, profile_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO benchmark_runs (run_name, language, profile_id, status)
        VALUES (?, ?, ?, 'running')
    """,
        (run_name, language, profile_id),
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id or 0


def update_benchmark_run_status(run_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE benchmark_runs SET status = ? WHERE id = ?
    """,
        (status, run_id),
    )
    conn.commit()
    conn.close()


def get_benchmark_runs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM benchmark_runs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_benchmark_result(run_id: int, file_path: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO benchmark_results (run_id, file_path, status)
        VALUES (?, ?, 'pending')
    """,
        (run_id, file_path),
    )
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return result_id or 0


def update_benchmark_result(
    result_id: int,
    status: str,
    final_transcript: str | None = None,
    error_message: str | None = None,
    ground_truth: str | None = None,
    wer: float | None = None,
    wer_errors: int | None = None,
    wer_words: int | None = None,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "UPDATE benchmark_results SET status = ?"
    params: list[Any] = [status]

    if final_transcript is not None:
        query += ", final_transcript = ?"
        params.append(final_transcript)

    if error_message is not None:
        query += ", error_message = ?"
        params.append(error_message)

    if ground_truth is not None:
        query += ", ground_truth = ?"
        params.append(ground_truth)

    if wer is not None:
        query += ", wer = ?"
        params.append(wer)

    if wer_errors is not None:
        query += ", wer_errors = ?"
        params.append(wer_errors)

    if wer_words is not None:
        query += ", wer_words = ?"
        params.append(wer_words)

    if status in ("completed", "error"):
        query += ", completed_at = CURRENT_TIMESTAMP"

    query += " WHERE id = ?"
    params.append(result_id)

    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()


def get_benchmark_results(run_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM benchmark_results WHERE run_id = ? ORDER BY created_at ASC",
        (run_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_transcriptions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transcriptions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_transcription_by_id(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transcriptions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_dictionary_profile(name: str, hotwords: list, replacements: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO dictionary_profiles (name, hotwords, replacements)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            hotwords=excluded.hotwords,
            replacements=excluded.replacements
    """,
        (name, json.dumps(hotwords), json.dumps(replacements)),
    )
    conn.commit()
    conn.close()


def get_dictionary_profiles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dictionary_profiles ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    profiles = []
    for row in rows:
        r = dict(row)
        r["hotwords"] = json.loads(r["hotwords"]) if r["hotwords"] else []
        r["replacements"] = json.loads(r["replacements"]) if r["replacements"] else []
        profiles.append(r)
    return profiles


def delete_dictionary_profile(profile_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dictionary_profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()


def save_ground_truth(file_path: str, text: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO benchmark_ground_truths (file_path, ground_truth)
        VALUES (?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            ground_truth=excluded.ground_truth,
            updated_at=CURRENT_TIMESTAMP
    """,
        (file_path, text),
    )
    conn.commit()
    conn.close()


def get_ground_truth(file_path: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ground_truth FROM benchmark_ground_truths WHERE file_path = ?",
        (file_path,),
    )
    row = cursor.fetchone()
    conn.close()
    return row["ground_truth"] if row else None


def get_all_ground_truths() -> set[str]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM benchmark_ground_truths")
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}
