import os
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")

FIXES_RE = re.compile(r"Fixes\s+#(\d+)", re.IGNORECASE)


def print_table(headers, rows):
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows) if rows else [0]) for i, h in enumerate(headers)]
    fmt = " | ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("-" * (sum(widths) + 3 * (len(headers) - 1)))
    for r in rows:
        print(fmt.format(*r))


def aggregate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # PRs per repo
    pr_counts = list(cur.execute("SELECT repo_name, COUNT(*) FROM pr GROUP BY repo_name ORDER BY repo_name"))

    # Issues per repo
    issue_counts = list(cur.execute("SELECT repo_name, COUNT(*) FROM issue GROUP BY repo_name ORDER BY repo_name"))

    # Map existing issues for quick lookup: {(repo, issue_number)}
    issue_set = set((r, n) for r, n in cur.execute("SELECT repo_name, issue_number FROM issue"))

    # Count fixes per PR
    pr_fixes = []
    for repo, pr_number, body in cur.execute("SELECT repo_name, pr_number, COALESCE(body, '') FROM pr"):
        numbers = set(int(m.group(1)) for m in FIXES_RE.finditer(body))
        matched = [n for n in numbers if (repo, n) in issue_set]
        pr_fixes.append((repo, pr_number, len(matched), ",".join(str(n) for n in sorted(matched)) or "-"))

    print("PRs per repo:")
    print_table(["repo", "pr_count"], pr_counts)
    print()
    print("Issues per repo:")
    print_table(["repo", "issue_count"], issue_counts)
    print()
    print("Fixes per PR:")
    print_table(["repo", "pr_number", "fixes_count", "issues_fixed"], pr_fixes)

    conn.close()


if __name__ == "__main__":
    aggregate()
