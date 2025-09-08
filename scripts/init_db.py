import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS pr (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_name TEXT NOT NULL,
        pr_number INTEGER NOT NULL,
        title TEXT,
        body TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS issue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_name TEXT NOT NULL,
        issue_number INTEGER NOT NULL,
        title TEXT,
        body TEXT
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
