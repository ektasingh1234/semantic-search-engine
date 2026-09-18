import sqlite3
import hashlib
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "users.db")


def init_users_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id TEXT PRIMARY KEY,
            username TEXT,
            query TEXT,
            answer TEXT,
            sources TEXT,
            latency REAL,
            search_mode TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_notes (
            id TEXT PRIMARY KEY,
            username TEXT,
            query TEXT,
            answer TEXT,
            sources TEXT,
            search_mode TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, email: str, password: str) -> dict:
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username.lower().strip(), email.lower().strip(), hash_password(password))
        )
        conn.commit()
        return {"success": True, "message": "Account created successfully!"}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return {"success": False, "message": "Username already taken."}
        elif "email" in str(e):
            return {"success": False, "message": "Email already registered."}
        return {"success": False, "message": "Registration failed."}
    finally:
        conn.close()

def login_user(username: str, password: str) -> dict:
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, email FROM users WHERE username=? AND password_hash=?",
        (username.lower().strip(), hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"success": True, "username": user[0], "email": user[1]}
    return {"success": False, "message": "Invalid username or password."}

# Persistence for Query History
def save_history_entry(username: str, entry: dict):
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO query_history 
           (id, username, query, answer, sources, latency, search_mode, timestamp) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            entry["id"],
            username.lower().strip(),
            entry["query"],
            entry["answer"],
            json.dumps(entry["sources"]),
            entry.get("time", 0.0),
            entry.get("mode", "wiki"),
            entry.get("timestamp", "")
        )
    )
    conn.commit()
    conn.close()

def fetch_user_history(username: str) -> list:
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, query, answer, sources, latency, search_mode, timestamp 
           FROM query_history WHERE username=? ORDER BY rowid DESC""",
        (username.lower().strip(),)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "query": r[1],
            "answer": r[2],
            "sources": json.loads(r[3]) if r[3] else [],
            "time": r[4],
            "mode": r[5],
            "timestamp": r[6]
        }
        for r in rows
    ]

def clear_user_history(username: str):
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM query_history WHERE username=?", (username.lower().strip(),))
    conn.commit()
    conn.close()

# Persistence for Saved Notes
def save_research_note(username: str, note: dict) -> bool:
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR REPLACE INTO saved_notes 
               (id, username, query, answer, sources, search_mode, timestamp) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                note["id"],
                username.lower().strip(),
                note["query"],
                note["answer"],
                json.dumps(note["sources"]),
                note.get("mode", "wiki"),
                note.get("timestamp", "")
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()

def fetch_user_saved_notes(username: str) -> list:
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, query, answer, sources, search_mode, timestamp 
           FROM saved_notes WHERE username=? ORDER BY rowid DESC""",
        (username.lower().strip(),)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "query": r[1],
            "answer": r[2],
            "sources": json.loads(r[3]) if r[3] else [],
            "mode": r[4],
            "timestamp": r[5]
        }
        for r in rows
    ]

def delete_saved_note(username: str, note_id: str):
    init_users_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_notes WHERE username=? AND id=?", (username.lower().strip(), note_id))
    conn.commit()
    conn.close()