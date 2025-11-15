from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Dict, Any, List, Optional

from flask import Flask, render_template, request, abort, jsonify, url_for

from data import load_datasets, DATASETS

app = Flask(__name__)

data_store = load_datasets()


def get_dataset(name: str) -> Dict[str, Any]:
    dataset = data_store.get(name)
    if not dataset:
        abort(404)
    return dataset


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return None


def filter_records(records: List[Dict[str, Any]], repo: Optional[str]) -> List[Dict[str, Any]]:
    if not repo:
        return records
    return [record for record in records if record.get("repo") == repo]


@lru_cache(maxsize=32)
def merged_repo_counts(repo: Optional[str]) -> List[Dict[str, Any]]:
    records = filter_records(get_dataset("merged_data")["records"], repo)
    counter = Counter(record.get("repo") for record in records if record.get("repo"))
    return [
        {"repo": repo_name, "count": count}
        for repo_name, count in counter.most_common(10)
    ]


@lru_cache(maxsize=32)
def merged_time_series(repo: Optional[str]) -> List[Dict[str, Any]]:
    records = filter_records(get_dataset("merged_data")["records"], repo)
    series: Dict[str, int] = defaultdict(int)
    for record in records:
        date = parse_date(record.get("created_at"))
        if date is None:
            continue
        key = date.strftime("%Y-%m-%d")
        series[key] += 1
    return [
        {"date": date, "count": series[date]}
        for date in sorted(series.keys())
    ]


@lru_cache(maxsize=32)
def closing_issue_distribution(repo: Optional[str]) -> List[Dict[str, Any]]:
    records = filter_records(get_dataset("pr_issue")["records"], repo)
    distribution: Dict[str, int] = defaultdict(int)
    for record in records:
        repo_name = record.get("repo") or "Unknown"
        closing = record.get("closing_issue", []) or []
        distribution[repo_name] += len(closing)
    return [
        {"repo": repo_name, "count": count}
        for repo_name, count in sorted(distribution.items(), key=lambda item: item[1], reverse=True)
    ]


@lru_cache(maxsize=32)
def pr_histogram(repo: Optional[str]) -> List[Dict[str, Any]]:
    records = filter_records(get_dataset("pr_detail")["records"], repo)
    bucket: Dict[str, int] = defaultdict(int)
    for record in records:
        date = parse_date(record.get("created_at"))
        if date is None:
            continue
        key = date.strftime("%Y-%m")
        bucket[key] += 1
    return [
        {"month": month, "count": bucket[month]}
        for month in sorted(bucket.keys())
    ]


@lru_cache(maxsize=32)
def issue_label_counts(repo: Optional[str]) -> List[Dict[str, Any]]:
    records = filter_records(get_dataset("issue_detail")["records"], repo)
    counter: Counter[str] = Counter()
    for record in records:
        labels = record.get("labels", []) or []
        for label in labels:
            if isinstance(label, dict):
                name = label.get("name")
            else:
                name = str(label)
            if name:
                counter[name] += 1
    return [
        {"label": label, "count": count}
        for label, count in counter.most_common(10)
    ]


def get_all_repos() -> List[str]:
    repos = set()
    for dataset in data_store.values():
        for record in dataset["records"]:
            repo_name = record.get("repo")
            if repo_name:
                repos.add(repo_name)
    return sorted(repos)


def build_related_links(dataset_name: str, record: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    related: Dict[str, List[Dict[str, str]]] = {}

    def add_related(target_dataset: str, target_record: Dict[str, Any], label: str) -> None:
        key_name = data_store[target_dataset]["primary_key"]
        key_value = target_record.get(key_name)
        if key_value is None:
            return
        related.setdefault(target_dataset, []).append(
            {
                "label": label,
                "url": url_for(
                    "dataset_detail",
                    dataset_name=target_dataset,
                    record_id=str(key_value),
                ),
            }
        )

    repo = record.get("repo")

    if dataset_name == "pr_detail":
        for issue in data_store["issue_detail"]["records"]:
            if (
                issue.get("repo") == repo
                and issue.get("number") in (record.get("linked_issues") or [])
            ):
                label = f"Issue #{issue.get('number')} - {issue.get('title', 'Issue')}"
                add_related("issue_detail", issue, label)
        for merged in data_store["merged_data"]["records"]:
            if merged.get("pr_id") == record.get("id"):
                label = (
                    f"Merged Entry #{merged.get('pull_number')}"
                )
                add_related("merged_data", merged, label)
        for pr_issue_entry in data_store["pr_issue"]["records"]:
            if (
                pr_issue_entry.get("repo") == repo
                and pr_issue_entry.get("pull_number") == record.get("number")
            ):
                label = f"Search Result #{pr_issue_entry.get('id')}"
                add_related("pr_issue", pr_issue_entry, label)

    elif dataset_name == "issue_detail":
        for pr in data_store["pr_detail"]["records"]:
            if (
                pr.get("repo") == repo
                and record.get("number") in (pr.get("linked_issues") or [])
            ):
                label = f"Pull Request #{pr.get('number')} - {pr.get('title', 'PR')}"
                add_related("pr_detail", pr, label)
        for merged in data_store["merged_data"]["records"]:
            if merged.get("issue_id") == record.get("id"):
                label = f"Merged Entry #{merged.get('pull_number')}"
                add_related("merged_data", merged, label)

    elif dataset_name == "pr_issue":
        for pr in data_store["pr_detail"]["records"]:
            if (
                pr.get("repo") == repo
                and pr.get("number") == record.get("pull_number")
            ):
                label = f"Pull Request #{pr.get('number')}"
                add_related("pr_detail", pr, label)
        for issue in data_store["issue_detail"]["records"]:
            if (
                issue.get("repo") == repo
                and issue.get("number") in (record.get("closing_issue") or [])
            ):
                label = f"Issue #{issue.get('number')}"
                add_related("issue_detail", issue, label)
        for merged in data_store["merged_data"]["records"]:
            if (
                merged.get("repo") == repo
                and merged.get("pull_number") == record.get("pull_number")
            ):
                label = f"Merged Entry #{merged.get('pull_number')}"
                add_related("merged_data", merged, label)

    elif dataset_name == "merged_data":
        for pr in data_store["pr_detail"]["records"]:
            if pr.get("id") == record.get("pr_id"):
                label = f"Pull Request #{pr.get('number')}"
                add_related("pr_detail", pr, label)
        for issue in data_store["issue_detail"]["records"]:
            if issue.get("id") == record.get("issue_id"):
                label = f"Issue #{issue.get('number')}"
                add_related("issue_detail", issue, label)
        for pr_issue_entry in data_store["pr_issue"]["records"]:
            if (
                pr_issue_entry.get("repo") == repo
                and pr_issue_entry.get("pull_number") == record.get("pull_number")
            ):
                label = f"Search Result #{pr_issue_entry.get('id')}"
                add_related("pr_issue", pr_issue_entry, label)

    return related


def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    if value is None:
        return "N/A"
    return str(value)


app.jinja_env.filters["format_value"] = format_value


@app.route("/")
def home() -> str:
    selected_dataset = request.args.get("dataset", "merged_data")
    dataset = get_dataset(selected_dataset)

    summary = {name: len(info["records"]) for name, info in data_store.items()}

    records = dataset["records"]
    fields = dataset["fields"]
    primary_key = dataset["primary_key"]

    return render_template(
        "home.html",
        datasets=DATASETS,
        summary=summary,
        selected_dataset=selected_dataset,
        records=records,
        fields=fields,
        primary_key=primary_key,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str) -> str:
    dataset = get_dataset(dataset_name)
    record = dataset["index"].get(record_id)
    if not record:
        abort(404)

    related = build_related_links(dataset_name, record)

    return render_template(
        "detail.html",
        dataset=dataset,
        record=record,
        related=related,
        datasets=DATASETS,
    )


@app.route("/visualize")
def visualize() -> str:
    repo_filter = request.args.get("repo")

    repo_counts = merged_repo_counts(repo_filter)
    time_series = merged_time_series(repo_filter)
    closing_issue_counts = closing_issue_distribution(repo_filter)
    histogram = pr_histogram(repo_filter)
    label_counts = issue_label_counts(repo_filter)

    return render_template(
        "visualize.html",
        repo_filter=repo_filter,
        available_repos=get_all_repos(),
        repo_counts=repo_counts,
        time_series=time_series,
        closing_issue_counts=closing_issue_counts,
        histogram=histogram,
        label_counts=label_counts,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    dataset = get_dataset(dataset_name)
    repo = request.args.get("repo")
    records = filter_records(dataset["records"], repo)
    return jsonify(records)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
