import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"

DATASET_FILES = {
    "pr_issue": {
        "path": DATA_DIR / "input_data" / "pr_issue_single.jsonl",
        "title": "PR Issue Search",
    },
    "pr_detail": {
        "path": DATA_DIR / "input_data" / "pr_detail.jsonl",
        "title": "PR Detail",
    },
    "issue_detail": {
        "path": DATA_DIR / "input_data" / "issue_detail.jsonl",
        "title": "Issue Detail",
    },
    "merged_data": {
        "path": DATA_DIR / "output_data" / "merged_data.jsonl",
        "title": "Merged Data",
    },
}

MERGED_DISPLAY_FIELDS = [
    "repo",
    "issue_number",
    "issue_title",
    "pull_number",
    "created_at",
]

app = Flask(__name__)


def load_jsonl(path: Path) -> List[Dict]:
    records: List[Dict] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def build_record_id(dataset_name: str, record: Dict, index: int) -> str:
    if dataset_name == "merged_data":
        repo = record.get("repo", "unknown")
        pull_number = record.get("pull_number", index)
        issue_number = record.get("issue_number", index)
        identifier = f"{repo}|{pull_number}|{issue_number}"
    else:
        if "id" in record:
            identifier = str(record["id"])
        elif dataset_name == "pr_detail":
            identifier = f"{record.get('repo', 'unknown')}|{record.get('pull_number', index)}"
        elif dataset_name == "issue_detail":
            identifier = f"{record.get('repo', 'unknown')}|{record.get('issue_number', index)}"
        else:
            identifier = f"{record.get('repo', 'unknown')}|{record.get('pull_number', index)}"
    return quote(str(identifier))


def detect_fields(dataset_name: str, records: List[Dict]) -> List[str]:
    if dataset_name == "merged_data":
        return MERGED_DISPLAY_FIELDS
    if not records:
        return []
    field_counter: Counter = Counter()
    for record in records:
        field_counter.update(record.keys())
    for field in ["_record_id", "_detail_url", "_detail_label"]:
        field_counter.pop(field, None)
    common_fields = [field for field, _ in field_counter.most_common()]
    return common_fields


def load_datasets() -> Dict[str, Dict]:
    datasets: Dict[str, Dict] = {}
    for name, meta in DATASET_FILES.items():
        records = load_jsonl(meta["path"])
        indexed_records: Dict[str, Dict] = {}
        for idx, record in enumerate(records):
            record_id = build_record_id(name, record, idx)
            record_copy = dict(record)
            record_copy["_record_id"] = record_id
            indexed_records[record_id] = record_copy
        datasets[name] = {
            "title": meta["title"],
            "path": meta["path"],
            "records": list(indexed_records.values()),
            "index": indexed_records,
            "fields": detect_fields(name, records),
        }
    return datasets


def group_by_repo(records: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for record in records:
        repo = record.get("repo", "unknown")
        groups[repo].append(record)
    return groups


def str_to_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


DATASETS = load_datasets()
GROUPED_REPOS = {name: group_by_repo(meta["records"]) for name, meta in DATASETS.items()}
ALL_REPOS = sorted(
    {
        record.get("repo")
        for meta in DATASETS.values()
        for record in meta["records"]
        if record.get("repo")
    }
)


def filter_by_repo(dataset_name: str, repo: Optional[str]) -> List[Dict]:
    records = DATASETS.get(dataset_name, {}).get("records", [])
    if not repo:
        return records
    return [record for record in records if record.get("repo") == repo]


def build_table_payload(dataset_name: str, records: List[Dict]) -> Tuple[List[str], List[Dict[str, str]]]:
    dataset = DATASETS.get(dataset_name)
    if not dataset:
        return [], []
    fields = dataset["fields"]
    if dataset_name == "merged_data":
        fields = MERGED_DISPLAY_FIELDS
    table_records: List[Dict[str, str]] = []
    for record in records:
        row = {field: record.get(field, "N/A") for field in fields}
        row["detail_url"] = url_for(
            "dataset_detail", dataset_name=dataset_name, record_id=record["_record_id"]
        )
        table_records.append(row)
    return fields, table_records


@lru_cache(maxsize=None)
def merged_repo_counts(repo: Optional[str] = None) -> Dict[str, int]:
    records = filter_by_repo("merged_data", repo)
    counts = Counter(record.get("repo", "unknown") for record in records)
    return dict(counts.most_common(10))


@lru_cache(maxsize=None)
def merged_time_series(repo: Optional[str] = None) -> Dict[str, int]:
    records = filter_by_repo("merged_data", repo)
    series = Counter()
    for record in records:
        created_at = str_to_date(record.get("created_at"))
        if created_at:
            key = created_at.date().isoformat()
            series[key] += 1
    return dict(sorted(series.items()))


@lru_cache(maxsize=None)
def closing_issue_distribution(repo: Optional[str] = None) -> Dict[str, int]:
    records = filter_by_repo("pr_issue", repo)
    counts = Counter(record.get("repo", "unknown") for record in records)
    return dict(counts)


@lru_cache(maxsize=None)
def pr_by_month(repo: Optional[str] = None) -> Dict[str, int]:
    records = filter_by_repo("pr_detail", repo)
    series = Counter()
    for record in records:
        created_at = str_to_date(record.get("created_at"))
        if created_at:
            key = created_at.strftime("%Y-%m")
            series[key] += 1
    return dict(sorted(series.items()))


@lru_cache(maxsize=None)
def top_issue_labels(repo: Optional[str] = None) -> Dict[str, int]:
    records = filter_by_repo("issue_detail", repo)
    label_counter = Counter()
    for record in records:
        labels = record.get("labels") or []
        if isinstance(labels, list):
            label_counter.update([str(label) for label in labels])
    return dict(label_counter.most_common(10))


def build_related_records(dataset_name: str, record: Dict) -> List[Tuple[str, Dict]]:
    related: List[Tuple[str, Dict]] = []
    repo = record.get("repo")
    issue_number = record.get("issue_number")
    pull_number = record.get("pull_number")

    if dataset_name == "pr_detail" and repo and issue_number:
        issue_records = DATASETS["issue_detail"]["records"]
        for issue in issue_records:
            if issue.get("repo") == repo and issue.get("issue_number") == issue_number:
                related.append(("issue_detail", issue))
        merged_records = DATASETS["merged_data"]["records"]
        for merged in merged_records:
            if (
                merged.get("repo") == repo
                and merged.get("pull_number") == pull_number
                and merged.get("issue_number") == issue_number
            ):
                related.append(("merged_data", merged))
    elif dataset_name == "issue_detail" and repo and issue_number:
        pr_records = DATASETS["pr_detail"]["records"]
        for pr in pr_records:
            if pr.get("repo") == repo and pr.get("issue_number") == issue_number:
                related.append(("pr_detail", pr))
        merged_records = DATASETS["merged_data"]["records"]
        for merged in merged_records:
            if merged.get("repo") == repo and merged.get("issue_number") == issue_number:
                related.append(("merged_data", merged))
    elif dataset_name == "merged_data":
        if repo and issue_number:
            issue_records = DATASETS["issue_detail"]["records"]
            for issue in issue_records:
                if issue.get("repo") == repo and issue.get("issue_number") == issue_number:
                    related.append(("issue_detail", issue))
        if repo and pull_number:
            pr_records = DATASETS["pr_detail"]["records"]
            for pr in pr_records:
                if pr.get("repo") == repo and pr.get("pull_number") == pull_number:
                    related.append(("pr_detail", pr))
        pr_issue_records = DATASETS["pr_issue"]["records"]
        for search_record in pr_issue_records:
            if (
                search_record.get("repo") == repo
                and search_record.get("pull_number") == pull_number
            ):
                related.append(("pr_issue", search_record))
    else:
        if repo and pull_number:
            pr_records = DATASETS["pr_detail"]["records"]
            for pr in pr_records:
                if pr.get("repo") == repo and pr.get("pull_number") == pull_number:
                    related.append(("pr_detail", pr))
        if repo and issue_number:
            issue_records = DATASETS["issue_detail"]["records"]
            for issue in issue_records:
                if issue.get("repo") == repo and issue.get("issue_number") == issue_number:
                    related.append(("issue_detail", issue))
    return related


@app.route("/")
def homepage():
    selected_dataset = request.args.get("dataset", "pr_issue")
    dataset = DATASETS.get(selected_dataset)
    if not dataset:
        return redirect(url_for("homepage", dataset="pr_issue"))

    repo_filter = request.args.get("repo")
    filtered_records = filter_by_repo(selected_dataset, repo_filter)
    table_fields, table_records = build_table_payload(selected_dataset, filtered_records)

    if repo_filter:
        summary_counts = {
            name: len(filter_by_repo(name, repo_filter)) for name in DATASETS.keys()
        }
    else:
        summary_counts = {name: len(meta["records"]) for name, meta in DATASETS.items()}

    return render_template(
        "index.html",
        datasets=DATASETS,
        selected_dataset=selected_dataset,
        table_fields=table_fields,
        table_records=table_records,
        repo_filter=repo_filter,
        summary_counts=summary_counts,
        available_repos=ALL_REPOS,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str):
    dataset = DATASETS.get(dataset_name)
    if not dataset:
        abort(404)
    decoded_id = unquote(record_id)
    record = dataset["index"].get(decoded_id)
    if not record:
        abort(404)
    related = build_related_records(dataset_name, record)
    return render_template(
        "detail.html",
        dataset_name=dataset_name,
        dataset_title=dataset["title"],
        record=record,
        related=related,
    )


@app.route("/visualize")
def visualize():
    repo_filter = request.args.get("repo")
    charts = {
        "merged_repo_counts": merged_repo_counts(repo=repo_filter),
        "merged_time_series": merged_time_series(repo=repo_filter),
        "closing_issue_distribution": closing_issue_distribution(repo=repo_filter),
        "pr_by_month": pr_by_month(repo=repo_filter),
        "top_issue_labels": top_issue_labels(repo=repo_filter),
    }
    return render_template(
        "visualize.html",
        charts=charts,
        repo_filter=repo_filter,
        available_repos=ALL_REPOS,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    dataset = DATASETS.get(dataset_name)
    if not dataset:
        abort(404)
    repo_filter = request.args.get("repo")
    records = filter_by_repo(dataset_name, repo_filter)
    fields = dataset["fields"]
    if dataset_name == "merged_data":
        fields = MERGED_DISPLAY_FIELDS
    data_rows: List[Dict[str, str]] = []
    for record in records:
        row = {field: record.get(field, "N/A") for field in fields}
        row["detail_url"] = url_for(
            "dataset_detail", dataset_name=dataset_name, record_id=record["_record_id"]
        )
        data_rows.append(row)
    return jsonify({"fields": fields, "records": data_rows})


@app.route("/api/summary")
def summary_api():
    repo_filter = request.args.get("repo")
    counts = {name: len(filter_by_repo(name, repo_filter)) for name in DATASETS.keys()}
    return jsonify({"counts": counts})


@app.context_processor
def inject_globals():
    return {"dataset_titles": {name: meta["title"] for name, meta in DATASETS.items()}}


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
