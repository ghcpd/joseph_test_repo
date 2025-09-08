import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")


def show_table(table_name: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        c = conn.cursor()
        # Validate table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        row = c.fetchone()
        if not row:
            print(f"Table '{table_name}' does not exist.")
            return

        c.execute(f"SELECT * FROM {table_name}")
        rows = c.fetchall()
        if not rows:
            print(f"Table '{table_name}' is empty.")
            return

        columns = rows[0].keys()
        # Compute column widths
        col_widths = {col: len(col) for col in columns}
        for r in rows:
            for col in columns:
                col_widths[col] = max(col_widths[col], len(str(r[col])))

        # Print header
        header = " | ".join(f"{col:{col_widths[col]}}" for col in columns)
        sep = "-+-".join("-" * col_widths[col] for col in columns)
        print(header)
        print(sep)

        # Print rows
        for r in rows:
            line = " | ".join(f"{str(r[col]):{col_widths[col]}}" for col in columns)
            print(line)
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/show_table.py <table_name>")
        sys.exit(1)
    show_table(sys.argv[1])
