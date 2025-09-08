import os
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "tracker.db")
INPUT_DIR = os.path.join(BASE_DIR, "input_data")

def load_jsonl(filename):
    path = os.path.join(INPUT_DIR, filename)
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def insert_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    prs = load_jsonl("pr_detail.jsonl")
    issues = load_jsonl("issue_detail.jsonl")

    for pr in prs:
        c.execute('''
        INSERT INTO pr (repo_name, pr_number, title, body)
        VALUES (?, ?, ?, ?)
        ''', (pr['repo_name'], pr['pr_number'], pr.get('title', ''), pr.get('body', '')))

    for issue in issues:
        c.execute('''
        INSERT INTO issue (repo_name, issue_number, title, body)
        VALUES (?, ?, ?, ?)
        ''', (issue['repo_name'], issue['issue_number'], issue.get('title', ''), issue.get('body', '')))

    conn.commit()
    conn.close()
    print("Data loaded successfully!")

if __name__ == "__main__":
    insert_data()
