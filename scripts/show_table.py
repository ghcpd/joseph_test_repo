import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")


def show_table(table_name: str) -> None:
    if not table_name:
        print("Usage: python scripts/show_table.py <table_name>")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cur.fetchone():
        print(f"Table '{table_name}' does not exist.")
        conn.close()
        sys.exit(1)

    rows = list(cur.execute(f"SELECT * FROM {table_name}"))
    if not rows:
        print(f"Table '{table_name}' is empty.")
        conn.close()
        return

    headers = rows[0].keys()
    print(" | ".join(headers))
    print("-" * (len(" | ".join(headers))))
    for row in rows:
        print(" | ".join(str(row[h]) for h in headers))

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/show_table.py <table_name>")
        sys.exit(1)
    show_table(sys.argv[1])
