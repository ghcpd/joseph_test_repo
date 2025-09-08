import os
import json
import sqlite3

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")
INPUT_DIR = os.path.join(BASE_DIR, "input_data")

def load_jsonl(filename):
    """Load data from a JSONL file.
    
    Args:
        filename: Name of the JSONL file in the input_data directory
    
    Returns:
        List of dictionaries containing the parsed JSON data
    """
    path = os.path.join(INPUT_DIR, filename)
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def insert_data():
    """Load PR and Issue data from JSONL files into the database.
    
    Uses INSERT OR IGNORE to prevent duplicate entries based on unique constraints.
    Safe to run multiple times - will only insert new data.
    Provides detailed reporting on what was inserted.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    prs = load_jsonl("pr_detail.jsonl")
    issues = load_jsonl("issue_detail.jsonl")

    # Track counts for reporting
    pr_inserted = 0
    issue_inserted = 0
    
    for pr in prs:
        c.execute('''
        INSERT OR IGNORE INTO pr (repo_name, pr_number, title, body)
        VALUES (?, ?, ?, ?)
        ''', (pr['repo_name'], pr['pr_number'], pr.get('title', ''), pr.get('body', '')))
        if c.rowcount > 0:
            pr_inserted += 1

    for issue in issues:
        c.execute('''
        INSERT OR IGNORE INTO issue (repo_name, issue_number, title, body)
        VALUES (?, ?, ?, ?)
        ''', (issue['repo_name'], issue['issue_number'], issue.get('title', ''), issue.get('body', '')))
        if c.rowcount > 0:
            issue_inserted += 1

    conn.commit()
    conn.close()
    print(f"Data loaded successfully! Inserted {pr_inserted} new PRs and {issue_inserted} new issues.")

if __name__ == "__main__":
    insert_data()
