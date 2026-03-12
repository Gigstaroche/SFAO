import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfao.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Main feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT    NOT NULL,
            text        TEXT    NOT NULL,
            sentiment   TEXT    NOT NULL,
            score       REAL    NOT NULL DEFAULT 0.0,
            category    TEXT    NOT NULL,
            urgency     TEXT    NOT NULL DEFAULT 'Low',
            status      TEXT    NOT NULL DEFAULT 'New',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Users table for the portal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("[DB] Vault initialized: sfao.db")

def insert_feedback(source, text, sentiment, score, category, urgency):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO feedback (source, text, sentiment, score, category, urgency)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (source, text, sentiment, score, category, urgency))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id

def get_all_feedback(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?
    ''', (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM feedback")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT sentiment, COUNT(*) as count FROM feedback GROUP BY sentiment")
    sentiments = {row['sentiment']: row['count'] for row in cursor.fetchall()}

    cursor.execute("SELECT category, COUNT(*) as count FROM feedback GROUP BY category")
    categories = {row['category']: row['count'] for row in cursor.fetchall()}

    cursor.execute("SELECT source, COUNT(*) as count FROM feedback GROUP BY source")
    sources = {row['source']: row['count'] for row in cursor.fetchall()}

    cursor.execute("SELECT urgency, COUNT(*) as count FROM feedback GROUP BY urgency")
    urgencies = {row['urgency']: row['count'] for row in cursor.fetchall()}

    conn.close()
    return {
        "total": total,
        "sentiments": sentiments,
        "categories": categories,
        "sources": sources,
        "urgencies": urgencies
    }

def update_status(feedback_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE feedback SET status = ? WHERE id = ?", (new_status, feedback_id))
    conn.commit()
    conn.close()

def insert_user(name, email, hashed_password, role='user'):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', (name, email, hashed_password, role))
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

if __name__ == "__main__":
    init_db()
