from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Tuple

from flask import Flask, abort, jsonify, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_CONFIG: Dict[str, Dict[str, Any]] = {
    "pr_issue": {
        "path": os.path.join("data", "input_data", "pr_issue_single.jsonl"),
        "id_field": "id",
    },
    "pr_detail": {
        "path": os.path.join("data", "input_data", "pr_detail.jsonl"),
        "id_field": "number",
    },
    "issue_detail": {
        "path": os.path.join("data", "input_data", "issue_detail.jsonl"),
        "id_field": "number",
    },
    "merged_data": {
        "path": os.path.join("data", "output_data", "merged_data.jsonl"),
        "id_field": None,
    },
}

DATASET_LABELS = {
    "pr_issue": "PR Issue Search Results",
    "pr_detail": "Pull Request Details",
    "issue_detail": "Issue Details",
    "merged_data": "Merged PR-Issue Data",
}

MERGED_DISPLAY_FIELDS = ["repo", "issue_number", "issue_title", "pull_number", "created_at"]

DATA_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}
DATA_ORDERED: Dict[str, List[Dict[str, Any]]] = {}
DATA_COLUMNS: Dict[str, List[str]] = {}

PR_DETAIL_BY_NUMBER: Dict[Tuple[str, Any], Dict[str, Any]] = {}
PR_DETAIL_BY_ID: Dict[str, Dict[str, Any]] = {}
ISSUE_DETAIL_BY_NUMBER: Dict[Tuple[str, Any], Dict[str, Any]] = {}
ISSUE_DETAIL_BY_ID: Dict[str, Dict[str, Any]] = {}
PR_ISSUE_BY_REPO_NUMBER: Dict[Tuple[str, Any], Dict[str, Any]] = {}
PR_ISSUE_BY_ID: Dict[str, Dict[str, Any]] = {}
MERGED_BY_PR_NUMBER: Dict[Tuple[str, Any], List[Dict[str, Any]]] = defaultdict(list)
MERGED_BY_PR_ID: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
MERGED_BY_ISSUE_NUMBER: Dict[Tuple[str, Any], List[Dict[str, Any]]] = defaultdict(list)
MERGED_BY_ISSUE_ID: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

ALL_REPOS: List[str] = []

app = Flask(__name__)


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
        return []
    return records


def extract_repo_name(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, str) and "repos/" in value:
        return value.split("repos/")[-1]
    return value if isinstance(value, str) else None


def determine_columns(records: List[Dict[str, Any]]) -> List[str]:
    if not records:
        return []
    columns: List[str] = []
    for record in records:
        for key in record.keys():
            if key == "_record_id":
                continue
            if key not in columns:
                columns.append(key)
    return columns


def normalize_repo_arg(repo: str | None) -> str:
    return repo if repo else "__all__"


def repo_from_arg(repo_arg: str) -> str | None:
    return None if repo_arg == "__all__" else repo_arg


def format_value_for_table(value: Any) -> Any:
    if value is None or value == "":
        return "N/A"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return value


def format_value_for_detail(value: Any) -> Any:
    if value is None or value == "":
        return "N/A"
    if isinstance(value, (list, dict)):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return value


def record_matches_repo(record: Dict[str, Any], repo: str | None) -> bool:
    if not repo:
        return True
    return record.get("repo") == repo


def clear_cached_data() -> None:
    merged_repo_counts.cache_clear()
    merged_pr_timeseries.cache_clear()
    pr_issue_closing_counts.cache_clear()
    pr_detail_month_hist.cache_clear()
    issue_top_labels.cache_clear()


def load_data() -> None:
    DATA_STORE.clear()
    DATA_ORDERED.clear()
    DATA_COLUMNS.clear()
    PR_DETAIL_BY_NUMBER.clear()
    PR_DETAIL_BY_ID.clear()
    ISSUE_DETAIL_BY_NUMBER.clear()
    ISSUE_DETAIL_BY_ID.clear()
    PR_ISSUE_BY_REPO_NUMBER.clear()
    PR_ISSUE_BY_ID.clear()
    MERGED_BY_PR_NUMBER.clear()
    MERGED_BY_PR_ID.clear()
    MERGED_BY_ISSUE_NUMBER.clear()
    MERGED_BY_ISSUE_ID.clear()

    repo_set = set()

    for dataset_name, config in DATA_CONFIG.items():
        path = os.path.join(BASE_DIR, config["path"])
        records = load_jsonl(path)
        dataset_map: Dict[str, Dict[str, Any]] = {}
        ordered_list: List[Dict[str, Any]] = []

        for record in records:
            record = dict(record)

            if dataset_name == "pr_issue":
                repo_name = record.get("repo") or extract_repo_name(record.get("repository_url"))
                record["repo"] = repo_name
                closing = record.get("closing_issue") or []
                record["closing_issue_count"] = len(closing)
            repo_value = record.get("repo")
            if repo_value:
                repo_set.add(repo_value)

            if dataset_name == "merged_data":
                repo = record.get("repo")
                pull_number = record.get("pull_number")
                issue_number = record.get("issue_number")
                record_id = f"{repo}|{pull_number}|{issue_number}"
            else:
                record_id = str(record.get(config["id_field"]))
            record["_record_id"] = record_id
            dataset_map[record_id] = record
            ordered_list.append(record)

        DATA_STORE[dataset_name] = dataset_map
        DATA_ORDERED[dataset_name] = ordered_list

        if dataset_name == "merged_data":
            DATA_COLUMNS[dataset_name] = MERGED_DISPLAY_FIELDS
        else:
            DATA_COLUMNS[dataset_name] = determine_columns(ordered_list)

    for record in DATA_ORDERED.get("pr_detail", []):
        repo = record.get("repo")
        number = record.get("number")
        pr_id = record.get("id")
        PR_DETAIL_BY_NUMBER[(repo, number)] = record
        PR_DETAIL_BY_ID[str(pr_id)] = record

    for record in DATA_ORDERED.get("issue_detail", []):
        repo = record.get("repo")
        number = record.get("number")
        issue_id = record.get("id")
        ISSUE_DETAIL_BY_NUMBER[(repo, number)] = record
        ISSUE_DETAIL_BY_ID[str(issue_id)] = record

    for record in DATA_ORDERED.get("pr_issue", []):
        repo = record.get("repo")
        number = record.get("number")
        pr_issue_id = record.get("id")
        PR_ISSUE_BY_REPO_NUMBER[(repo, number)] = record
        PR_ISSUE_BY_ID[str(pr_issue_id)] = record

    for record in DATA_ORDERED.get("merged_data", []):
        repo = record.get("repo")
        pull_number = record.get("pull_number")
        issue_number = record.get("issue_number")
        pr_id = record.get("pr_record_id")
        issue_id = record.get("issue_record_id")

        MERGED_BY_PR_NUMBER[(repo, pull_number)].append(record)
        if pr_id is not None:
            MERGED_BY_PR_ID[str(pr_id)].append(record)
        MERGED_BY_ISSUE_NUMBER[(repo, issue_number)].append(record)
        if issue_id is not None:
            MERGED_BY_ISSUE_ID[str(issue_id)].append(record)

    global ALL_REPOS
    ALL_REPOS = sorted(repo_set)

    clear_cached_data()


def build_related_entries(dataset_name: str, record: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    related: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    repo = record.get("repo")

    if dataset_name == "pr_detail":
        issue_number = record.get("related_issue_number")
        if repo and issue_number is not None:
            issue = ISSUE_DETAIL_BY_NUMBER.get((repo, issue_number))
            if issue:
                related["Related Issues"].append(
                    {
                        "text": f"Issue #{issue.get('number')}: {issue.get('title')}",
                        "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue.get("_record_id")),
                    }
                )
        pr_issue = PR_ISSUE_BY_REPO_NUMBER.get((repo, record.get("number")))
        if pr_issue:
            related["PR Issue Search"].append(
                {
                    "text": f"Search Record #{pr_issue.get('id')}",
                    "url": url_for("dataset_detail", dataset_name="pr_issue", record_id=pr_issue.get("_record_id")),
                }
            )
        for merged in MERGED_BY_PR_NUMBER.get((repo, record.get("number")), []):
            related["Merged Data"].append(
                {
                    "text": f"{merged.get('repo')} - Issue #{merged.get('issue_number')} / PR #{merged.get('pull_number')}",
                    "url": url_for("dataset_detail", dataset_name="merged_data", record_id=merged.get("_record_id")),
                }
            )

    elif dataset_name == "issue_detail":
        for pr_number in record.get("related_pr_numbers", []):
            pr_detail = PR_DETAIL_BY_NUMBER.get((repo, pr_number))
            if pr_detail:
                related["Related PRs"].append(
                    {
                        "text": f"PR #{pr_detail.get('number')}: {pr_detail.get('title')}",
                        "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_detail.get("_record_id")),
                    }
                )
        for merged in MERGED_BY_ISSUE_NUMBER.get((repo, record.get("number")), []):
            related["Merged Data"].append(
                {
                    "text": f"{merged.get('repo')} - Issue #{merged.get('issue_number')} / PR #{merged.get('pull_number')}",
                    "url": url_for("dataset_detail", dataset_name="merged_data", record_id=merged.get("_record_id")),
                }
            )

    elif dataset_name == "pr_issue":
        pr_detail = PR_DETAIL_BY_NUMBER.get((repo, record.get("number")))
        if pr_detail:
            related["Pull Request Detail"].append(
                {
                    "text": f"PR #{pr_detail.get('number')}: {pr_detail.get('title')}",
                    "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_detail.get("_record_id")),
                }
            )
        closing_issue_entries = record.get("closing_issue") or []
        for issue_entry in closing_issue_entries:
            issue_repo = issue_entry.get("repo") or repo
            issue_number = issue_entry.get("number")
            issue_detail = ISSUE_DETAIL_BY_NUMBER.get((issue_repo, issue_number))
            if issue_detail:
                related["Closing Issues"].append(
                    {
                        "text": f"Issue #{issue_detail.get('number')}: {issue_detail.get('title')}",
                        "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_detail.get("_record_id")),
                    }
                )
        for merged in MERGED_BY_PR_NUMBER.get((repo, record.get("number")), []):
            related["Merged Data"].append(
                {
                    "text": f"{merged.get('repo')} - Issue #{merged.get('issue_number')} / PR #{merged.get('pull_number')}",
                    "url": url_for("dataset_detail", dataset_name="merged_data", record_id=merged.get("_record_id")),
                }
            )

    elif dataset_name == "merged_data":
        pr_id = record.get("pr_record_id")
        issue_id = record.get("issue_record_id")
        repo = record.get("repo")
        pr_detail = None
        if pr_id is not None:
            pr_detail = PR_DETAIL_BY_ID.get(str(pr_id))
        if not pr_detail and repo:
            pr_detail = PR_DETAIL_BY_NUMBER.get((repo, record.get("pull_number")))
        if pr_detail:
            related["Pull Request Detail"].append(
                {
                    "text": f"PR #{pr_detail.get('number')}: {pr_detail.get('title')}",
                    "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_detail.get("_record_id")),
                }
            )
        issue_detail = None
        if issue_id is not None:
            issue_detail = ISSUE_DETAIL_BY_ID.get(str(issue_id))
        if not issue_detail and repo:
            issue_detail = ISSUE_DETAIL_BY_NUMBER.get((repo, record.get("issue_number")))
        if issue_detail:
            related["Issue Detail"].append(
                {
                    "text": f"Issue #{issue_detail.get('number')}: {issue_detail.get('title')}",
                    "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_detail.get("_record_id")),
                }
            )
        pr_issue = PR_ISSUE_BY_REPO_NUMBER.get((repo, record.get("pull_number")))
        if pr_issue:
            related["PR Issue Search"].append(
                {
                    "text": f"Search Record #{pr_issue.get('id')}",
                    "url": url_for("dataset_detail", dataset_name="pr_issue", record_id=pr_issue.get("_record_id")),
                }
            )

    return related


@app.route("/")
def dashboard():
    dataset_name = request.args.get("dataset", "merged_data")
    if dataset_name not in DATA_STORE:
        dataset_name = "merged_data"
    dataset_records = DATA_ORDERED.get(dataset_name, [])
    display_columns = DATA_COLUMNS.get(dataset_name, [])

    summaries = {name: len(records) for name, records in DATA_ORDERED.items()}

    return render_template(
        "index.html",
        dataset_name=dataset_name,
        dataset_labels=DATASET_LABELS,
        dataset_records=dataset_records,
        display_columns=display_columns,
        summaries=summaries,
        format_value=format_value_for_table,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str):
    dataset = DATA_STORE.get(dataset_name)
    if dataset is None:
        abort(404)
    record = dataset.get(record_id)
    if record is None:
        abort(404)

    related_entries = build_related_entries(dataset_name, record)

    return render_template(
        "detail.html",
        dataset_name=dataset_name,
        dataset_labels=DATASET_LABELS,
        record=record,
        related_entries=related_entries,
        format_value=format_value_for_detail,
    )


def parse_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


@lru_cache(maxsize=64)
def merged_repo_counts(repo_arg: str) -> Dict[str, List[Any]]:
    repo_filter = repo_from_arg(repo_arg)
    counter: Counter[str] = Counter()
    for record in DATA_ORDERED.get("merged_data", []):
        if repo_filter and record.get("repo") != repo_filter:
            continue
        repo_name = record.get("repo") or "Unknown"
        counter[repo_name] += 1
    top_items = counter.most_common(10)
    labels = [item for item, _ in top_items]
    values = [count for _, count in top_items]
    return {"labels": labels, "values": values}


@lru_cache(maxsize=64)
def merged_pr_timeseries(repo_arg: str) -> Dict[str, List[Any]]:
    repo_filter = repo_from_arg(repo_arg)
    counter: Counter[str] = Counter()
    for record in DATA_ORDERED.get("merged_data", []):
        if repo_filter and record.get("repo") != repo_filter:
            continue
        dt = parse_datetime(record.get("created_at"))
        if not dt:
            continue
        counter[dt.date().isoformat()] += 1
    dates = sorted(counter.keys())
    counts = [counter[date] for date in dates]
    return {"dates": dates, "counts": counts}


@lru_cache(maxsize=64)
def pr_issue_closing_counts(repo_arg: str) -> Dict[str, List[Any]]:
    repo_filter = repo_from_arg(repo_arg)
    counter: Counter[str] = Counter()
    for record in DATA_ORDERED.get("pr_issue", []):
        repo_name = record.get("repo")
        if repo_filter and repo_name != repo_filter:
            continue
        closing = record.get("closing_issue") or []
        counter[repo_name or "Unknown"] += len(closing)
    items = counter.most_common()
    labels = [item for item, _ in items]
    values = [count for _, count in items]
    return {"labels": labels, "values": values}


@lru_cache(maxsize=64)
def pr_detail_month_hist(repo_arg: str) -> Dict[str, List[Any]]:
    repo_filter = repo_from_arg(repo_arg)
    counter: Counter[str] = Counter()
    for record in DATA_ORDERED.get("pr_detail", []):
        if repo_filter and record.get("repo") != repo_filter:
            continue
        dt = parse_datetime(record.get("created_at"))
        if not dt:
            continue
        counter[dt.strftime("%Y-%m")] += 1
    months = sorted(counter.keys())
    values = [counter[month] for month in months]
    return {"labels": months, "values": values}


@lru_cache(maxsize=64)
def issue_top_labels(repo_arg: str) -> Dict[str, List[Any]]:
    repo_filter = repo_from_arg(repo_arg)
    counter: Counter[str] = Counter()
    for record in DATA_ORDERED.get("issue_detail", []):
        if repo_filter and record.get("repo") != repo_filter:
            continue
        labels = record.get("labels") or []
        for label in labels:
            counter[label] += 1
    top_items = counter.most_common(10)
    labels = [item for item, _ in top_items]
    values = [count for _, count in top_items]
    return {"labels": labels, "values": values}


@app.route("/visualize")
def visualize():
    repo_filter = request.args.get("repo")
    repo_arg = normalize_repo_arg(repo_filter)

    charts = {
        "merged_repo_counts": merged_repo_counts(repo_arg),
        "merged_pr_timeseries": merged_pr_timeseries(repo_arg),
        "pr_issue_closing_counts": pr_issue_closing_counts(repo_arg),
        "pr_detail_month_hist": pr_detail_month_hist(repo_arg),
        "issue_top_labels": issue_top_labels(repo_arg),
    }

    return render_template(
        "visualize.html",
        dataset_labels=DATASET_LABELS,
        repo_filter=repo_filter,
        charts=charts,
        available_repos=ALL_REPOS,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    dataset = DATA_ORDERED.get(dataset_name)
    if dataset is None:
        abort(404)
    repo_filter = request.args.get("repo")
    filtered_records = [record for record in dataset if record_matches_repo(record, repo_filter)]
    return jsonify(filtered_records)


load_data()


if __name__ == "__main__":
    app.run(debug=True)
