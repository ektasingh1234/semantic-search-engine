import sqlite3
import hashlib
import os

DB_PATH = "users.db"

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