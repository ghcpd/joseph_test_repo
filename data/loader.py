from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent.parent

DATASETS: Dict[str, Dict[str, Any]] = {
    "pr_issue": {
        "label": "PR Search Results",
        "path": Path("input_data/pr_issue_single.jsonl"),
        "primary_key": "id",
        "display_fields": None,
    },
    "pr_detail": {
        "label": "Pull Request Details",
        "path": Path("input_data/pr_detail.jsonl"),
        "primary_key": "id",
        "display_fields": None,
    },
    "issue_detail": {
        "label": "Issue Details",
        "path": Path("input_data/issue_detail.jsonl"),
        "primary_key": "id",
        "display_fields": None,
    },
    "merged_data": {
        "label": "Merged PR/Issue Data",
        "path": Path("output_data/merged_data.jsonl"),
        "primary_key": "pr_id",
        "display_fields": [
            "repo",
            "issue_number",
            "issue_title",
            "pull_number",
            "created_at",
        ],
    },
}


def _load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []

    records: List[Dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            records.append(record)
    return records


def _index_records(records: List[Dict[str, Any]], primary_key: str) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for record in records:
        value = record.get(primary_key)
        if value is None:
            continue
        index[str(value)] = record
    return index


def _collect_fields(records: List[Dict[str, Any]]) -> List[str]:
    fields = set()
    for record in records:
        fields.update(record.keys())
    return sorted(fields)


@lru_cache(maxsize=1)
def load_datasets() -> Dict[str, Dict[str, Any]]:
    datasets: Dict[str, Dict[str, Any]] = {}
    for name, config in DATASETS.items():
        file_path = BASE_DIR / config["path"]
        records = _load_jsonl(file_path)
        index = _index_records(records, config["primary_key"])
        fields = config["display_fields"] or _collect_fields(records)
        datasets[name] = {
            "name": name,
            "label": config["label"],
            "records": records,
            "index": index,
            "fields": fields,
            "primary_key": config["primary_key"],
        }
    return datasets
