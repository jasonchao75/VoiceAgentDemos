import sqlite3
import os
import json
from pathlib import Path

DB_DIR = Path(__file__).parent / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "transcriptions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            language TEXT,
            final_transcript TEXT,
            audio_file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionary_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            hotwords TEXT,
            replacements TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_transcription(session_id: str, language: str, final_transcript: str, audio_file_path: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO transcriptions (session_id, language, final_transcript, audio_file_path)
        VALUES (?, ?, ?, ?)
    ''', (session_id, language, final_transcript, audio_file_path))
    conn.commit()
    conn.close()

def get_all_transcriptions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transcriptions ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_dictionary_profile(name: str, hotwords: list, replacements: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dictionary_profiles (name, hotwords, replacements)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            hotwords=excluded.hotwords,
            replacements=excluded.replacements
    ''', (name, json.dumps(hotwords), json.dumps(replacements)))
    conn.commit()
    conn.close()

def get_dictionary_profiles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dictionary_profiles ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    profiles = []
    for row in rows:
        r = dict(row)
        r['hotwords'] = json.loads(r['hotwords']) if r['hotwords'] else []
        r['replacements'] = json.loads(r['replacements']) if r['replacements'] else []
        profiles.append(r)
    return profiles

def delete_dictionary_profile(profile_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM dictionary_profiles WHERE id = ?', (profile_id,))
    conn.commit()
    conn.close()
