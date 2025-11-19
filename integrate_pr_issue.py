"""Utility script to merge PR, issue, and search datasets.

This script demonstrates how the example JSONL files relate to one another. It reads
`pr_detail.jsonl`, `issue_detail.jsonl`, and `pr_issue_single.jsonl` and writes a
new `merged_data.jsonl` file to `data/output_data/`.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "data", "input_data")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "output_data", "merged_data.jsonl")


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                records.append(json.loads(raw))
    except FileNotFoundError:
        raise RuntimeError(f"Missing data file: {path}")
    return records


def write_jsonl(path: str, records: Iterable[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_repo_name(repository_url: str | None) -> str | None:
    if not repository_url:
        return None
    if "repos/" in repository_url:
        return repository_url.split("repos/")[-1]
    return repository_url


def integrate() -> List[Dict[str, Any]]:
    pr_details = load_jsonl(os.path.join(INPUT_DIR, "pr_detail.jsonl"))
    issue_details = load_jsonl(os.path.join(INPUT_DIR, "issue_detail.jsonl"))
    pr_search = load_jsonl(os.path.join(INPUT_DIR, "pr_issue_single.jsonl"))

    issue_index: Dict[Tuple[str, Any], Dict[str, Any]] = {}
    for issue in issue_details:
        repo = issue.get("repo")
        number = issue.get("number")
        if repo is not None and number is not None:
            issue_index[(repo, number)] = issue

    pr_lookup: Dict[Tuple[str, Any], Dict[str, Any]] = {}
    for pr in pr_details:
        repo = pr.get("repo")
        number = pr.get("number")
        if repo is not None and number is not None:
            pr_lookup[(repo, number)] = pr

    # Augment PR search data with repo names for downstream use
    for pr_issue in pr_search:
        repo_name = pr_issue.get("repo")
        if not repo_name:
            repo_name = extract_repo_name(pr_issue.get("repository_url"))
            if repo_name:
                pr_issue["repo"] = repo_name

    merged_records: List[Dict[str, Any]] = []
    for pr in pr_details:
        repo = pr.get("repo")
        issue_number = pr.get("related_issue_number")
        pull_number = pr.get("number")
        if repo is None or issue_number is None or pull_number is None:
            continue

        issue_record = issue_index.get((repo, issue_number))
        if not issue_record:
            continue

        merged_record = {
            "repo": repo,
            "issue_number": issue_record.get("number"),
            "issue_title": issue_record.get("title"),
            "pull_number": pull_number,
            "pull_title": pr.get("title"),
            "created_at": pr.get("created_at"),
            "issue_record_id": issue_record.get("id"),
            "pr_record_id": pr.get("id"),
        }

        merged_records.append(merged_record)

    return merged_records


def main() -> None:
    merged_records = integrate()
    write_jsonl(OUTPUT_PATH, merged_records)
    print(f"Wrote {len(merged_records)} merged records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
