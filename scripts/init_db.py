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

    # Deduplicate existing records by keeping the smallest id per unique key
    c.execute('''
    DELETE FROM pr
    WHERE id NOT IN (
        SELECT MIN(id) FROM pr GROUP BY repo_name, pr_number
    )
    ''')
    c.execute('''
    DELETE FROM issue
    WHERE id NOT IN (
        SELECT MIN(id) FROM issue GROUP BY repo_name, issue_number
    )
    ''')

    # Add unique indexes to enforce idempotency on (repo_name, pr_number/issue_number)
    c.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_pr_unique
    ON pr(repo_name, pr_number)
    ''')
    c.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_issue_unique
    ON issue(repo_name, issue_number)
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
