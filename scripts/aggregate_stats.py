import os
import re
import sqlite3
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")

FIXES_PATTERN = re.compile(r"Fixes\s*#(\d+)", re.IGNORECASE)


def aggregate_stats():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        c = conn.cursor()

        # Per-repo counts for PRs and Issues
        c.execute("SELECT repo_name, COUNT(*) as pr_count FROM pr GROUP BY repo_name")
        pr_counts = {row["repo_name"]: row["pr_count"] for row in c.fetchall()}

        c.execute("SELECT repo_name, COUNT(*) as issue_count FROM issue GROUP BY repo_name")
        issue_counts = {row["repo_name"]: row["issue_count"] for row in c.fetchall()}

        # Issues fixed per PR based on body
        c.execute("SELECT repo_name, pr_number, body FROM pr")
        pr_fix_counts = {}
        for row in c.fetchall():
            body = row["body"] or ""
            matches = FIXES_PATTERN.findall(body)
            pr_fix_counts[(row["repo_name"], row["pr_number"])] = len(matches)

        # Prepare formatted output
        repos = sorted(set(pr_counts.keys()) | set(issue_counts.keys()))
        if not repos:
            print("No data available.")
            return

        # Table for per-repo counts
        print("Per-repo PR and Issue counts:")
        headers = ["repo_name", "pr_count", "issue_count"]
        rows = []
        for repo in repos:
            rows.append({
                "repo_name": repo,
                "pr_count": pr_counts.get(repo, 0),
                "issue_count": issue_counts.get(repo, 0),
            })
        _print_table(headers, rows)

        # Table for PR fix counts
        print("\nIssues fixed per PR:")
        headers = ["repo_name", "pr_number", "fixes_count"]
        rows = []
        for (repo, pr_number), cnt in sorted(pr_fix_counts.items()):
            rows.append({
                "repo_name": repo,
                "pr_number": pr_number,
                "fixes_count": cnt,
            })
        _print_table(headers, rows)

    finally:
        conn.close()


def _print_table(headers, rows):
    if not rows:
        print("No rows to display.")
        return
    col_widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(r[h])))

    header_line = " | ".join(f"{h:{col_widths[h]}}" for h in headers)
    sep = "-+-".join("-" * col_widths[h] for h in headers)
    print(header_line)
    print(sep)
    for r in rows:
        line = " | ".join(f"{str(r[h]):{col_widths[h]}}" for h in headers)
        print(line)


if __name__ == "__main__":
    aggregate_stats()
