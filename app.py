import json
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from flask import Flask, abort, jsonify, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_CONFIG = {
    "pr_issue": {
        "path": BASE_DIR / "input_data" / "pr_issue_single.jsonl",
        "title": "PR Issue Search Results",
        "display_fields": None,
    },
    "pr_detail": {
        "path": BASE_DIR / "input_data" / "pr_detail.jsonl",
        "title": "Pull Request Details",
        "display_fields": None,
    },
    "issue_detail": {
        "path": BASE_DIR / "input_data" / "issue_detail.jsonl",
        "title": "Issue Details",
        "display_fields": None,
    },
    "merged_data": {
        "path": BASE_DIR / "output_data" / "merged_data.jsonl",
        "title": "Merged PR-Issue Data",
        "display_fields": ["repo", "issue_number", "issue_title", "pull_number", "created_at"],
    },
}

app = Flask(__name__)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def determine_record_id(dataset: str, record: Dict[str, Any], fallback_index: int) -> str:
    preferred_keys = [
        "id",
        "number",
        "node_id",
        "pull_number",
        "issue_number",
        "url",
    ]
    for key in preferred_keys:
        value = record.get(key)
        if value is not None:
            return str(value)
    if dataset == "merged_data":
        repo = record.get("repo", "repo")
        issue_number = record.get("issue_number")
        pull_number = record.get("pull_number")
        return f"{repo}:{issue_number}:{pull_number}"
    return f"{dataset}-{fallback_index}"


def extract_repo(record: Dict[str, Any]) -> Optional[str]:
    if "repo" in record and isinstance(record["repo"], str):
        return record["repo"]
    repo_data = record.get("base") or record.get("head")
    if isinstance(repo_data, dict):
        nested = repo_data.get("repo")
        if isinstance(nested, dict):
            return nested.get("full_name")
    return None


def flatten_for_display(record: Dict[str, Any]) -> Dict[str, Any]:
    display_record: Dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (dict, list)):
            display_record[key] = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            display_record[key] = value if value not in (None, "") else "N/A"
    return display_record


def detect_display_fields(records: Iterable[Dict[str, Any]]) -> List[str]:
    first_record = next(iter(records), None)
    if not first_record:
        return []
    return [key for key in first_record.keys() if key != "_record_id"]


def build_dataset() -> Dict[str, Dict[str, Any]]:
    datasets: Dict[str, Dict[str, Any]] = {}
    for name, cfg in DATA_CONFIG.items():
        records = load_jsonl(cfg["path"])
        indexed_records: Dict[str, Dict[str, Any]] = {}
        for idx, record in enumerate(records):
            record_id = determine_record_id(name, record, idx)
            record["_record_id"] = record_id
            indexed_records[record_id] = record
        display_fields = cfg["display_fields"] or detect_display_fields(records)
        datasets[name] = {
            "title": cfg["title"],
            "records": records,
            "index": indexed_records,
            "display_fields": display_fields,
        }
    return datasets


def build_cross_references(datasets: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[Any, Dict[str, Any]]]:
    pr_by_repo_number: Dict[tuple, Dict[str, Any]] = {}
    issue_by_repo_number: Dict[tuple, Dict[str, Any]] = {}
    pr_issue_by_repo_pull: Dict[tuple, Dict[str, Any]] = {}
    merged_lookup: Dict[tuple, Dict[str, Any]] = {}

    for record in datasets["pr_detail"]["records"]:
        repo = extract_repo(record) or record.get("repo")
        number = record.get("number")
        if repo and number is not None:
            pr_by_repo_number[(repo, int(number))] = record

    for record in datasets["issue_detail"]["records"]:
        repo = extract_repo(record) or record.get("repo")
        number = record.get("number")
        if repo and number is not None:
            issue_by_repo_number[(repo, int(number))] = record

    for record in datasets["pr_issue"]["records"]:
        repo = extract_repo(record) or record.get("repo")
        pull_number = record.get("pull_number")
        if repo and pull_number is not None:
            pr_issue_by_repo_pull[(repo, int(pull_number))] = record

    for record in datasets["merged_data"]["records"]:
        repo = record.get("repo")
        issue_number = record.get("issue_number")
        pull_number = record.get("pull_number")
        if repo and issue_number is not None and pull_number is not None:
            merged_lookup[(repo, int(pull_number), int(issue_number))] = record

    return {
        "pr_by_repo_number": pr_by_repo_number,
        "issue_by_repo_number": issue_by_repo_number,
        "pr_issue_by_repo_pull": pr_issue_by_repo_pull,
        "merged_lookup": merged_lookup,
    }


datasets = build_dataset()
cross_refs = build_cross_references(datasets)


@app.context_processor
def inject_globals() -> Dict[str, Any]:
    return {"dataset_config": DATA_CONFIG}


def get_dataset_or_404(dataset_name: str) -> Dict[str, Any]:
    dataset = datasets.get(dataset_name)
    if not dataset:
        abort(404, description="Dataset not found")
    return dataset


def filter_by_repo(records: List[Dict[str, Any]], repo: Optional[str]) -> List[Dict[str, Any]]:
    if not repo:
        return records
    repo_lower = repo.lower()
    filtered: List[Dict[str, Any]] = []
    for record in records:
        record_repo = extract_repo(record) or str(record.get("repo", ""))
        if record_repo and record_repo.lower() == repo_lower:
            filtered.append(record)
    return filtered


def get_related_entries(dataset_name: str, record: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    related: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    repo = extract_repo(record) or record.get("repo")
    if dataset_name == "pr_detail" and repo:
        number = record.get("number")
        if number is not None:
            pr_issue_record = cross_refs["pr_issue_by_repo_pull"].get((repo, int(number)))
            if pr_issue_record:
                closing_issue = pr_issue_record.get("closing_issue")
                related_issue = cross_refs["issue_by_repo_number"].get((repo, int(closing_issue))) if closing_issue is not None else None
                if related_issue:
                    related["issue_detail"].append(
                        {
                            "label": related_issue.get("title", "Linked Issue"),
                            "url": url_for(
                                "dataset_detail",
                                dataset_name="issue_detail",
                                record_id=related_issue["_record_id"],
                            ),
                        }
                    )
    elif dataset_name == "issue_detail" and repo:
        number = record.get("number")
        if number is not None:
            for (repo_key, pull_number), pr_issue_record in cross_refs["pr_issue_by_repo_pull"].items():
                if repo_key == repo and int(pr_issue_record.get("closing_issue", -1)) == int(number):
                    pr_record = cross_refs["pr_by_repo_number"].get((repo, int(pull_number)))
                    if pr_record:
                        related["pr_detail"].append(
                            {
                                "label": pr_record.get("title", "Related PR"),
                                "url": url_for(
                                    "dataset_detail",
                                    dataset_name="pr_detail",
                                    record_id=pr_record["_record_id"],
                                ),
                            }
                        )
                    related["pr_issue"].append(
                        {
                            "label": pr_issue_record.get("title", "PR Search Result"),
                            "url": url_for(
                                "dataset_detail",
                                dataset_name="pr_issue",
                                record_id=pr_issue_record["_record_id"],
                            ),
                        }
                    )
    elif dataset_name == "merged_data" and repo:
        issue_number = record.get("issue_number")
        pull_number = record.get("pull_number")
        if issue_number is not None and pull_number is not None:
            issue_record = cross_refs["issue_by_repo_number"].get((repo, int(issue_number)))
            pr_record = cross_refs["pr_by_repo_number"].get((repo, int(pull_number)))
            pr_issue_record = cross_refs["pr_issue_by_repo_pull"].get((repo, int(pull_number)))
            if issue_record:
                related["issue_detail"].append(
                    {
                        "label": issue_record.get("title", "Linked Issue"),
                        "url": url_for(
                            "dataset_detail",
                            dataset_name="issue_detail",
                            record_id=issue_record["_record_id"],
                        ),
                    }
                )
            if pr_record:
                related["pr_detail"].append(
                    {
                        "label": pr_record.get("title", "Linked PR"),
                        "url": url_for(
                            "dataset_detail",
                            dataset_name="pr_detail",
                            record_id=pr_record["_record_id"],
                        ),
                    }
                )
            if pr_issue_record:
                related["pr_issue"].append(
                    {
                        "label": pr_issue_record.get("title", "PR Issue"),
                        "url": url_for(
                            "dataset_detail",
                            dataset_name="pr_issue",
                            record_id=pr_issue_record["_record_id"],
                        ),
                    }
                )
    return related


@app.route("/")
def index():
    selected_dataset = request.args.get("dataset", "merged_data")
    dataset = get_dataset_or_404(selected_dataset)
    summary_cards = {
        name: {
            "title": info["title"],
            "count": len(info["records"]),
        }
        for name, info in datasets.items()
    }
    display_fields = dataset["display_fields"]
    records = dataset["records"]
    table_rows = []
    for record in records:
        row = {
            "values_list": [flatten_for_display(record).get(field, "N/A") for field in display_fields],
            "detail_url": url_for(
                "dataset_detail", dataset_name=selected_dataset, record_id=record["_record_id"]
            ),
        }
        table_rows.append(row)
    return render_template(
        "index.html",
        selected_dataset=selected_dataset,
        datasets=datasets,
        summary_cards=summary_cards,
        display_fields=display_fields,
        table_rows=table_rows,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str):
    dataset = get_dataset_or_404(dataset_name)
    record = dataset["index"].get(record_id)
    if not record:
        abort(404, description="Record not found")
    display_record = flatten_for_display(record)
    related = get_related_entries(dataset_name, record)
    return render_template(
        "detail.html",
        dataset_name=dataset_name,
        dataset_title=dataset["title"],
        record=display_record,
        related=related,
        datasets=datasets,
    )


def parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@lru_cache(maxsize=64)
def compute_visualization_data(repo_filter: Optional[str]) -> Dict[str, Any]:
    repo_filter = repo_filter or ""
    repo_filter_normalized = repo_filter.strip() or None
    merged_records = filter_by_repo(datasets["merged_data"]["records"], repo_filter_normalized)
    pr_issue_records = filter_by_repo(datasets["pr_issue"]["records"], repo_filter_normalized)
    pr_detail_records = filter_by_repo(datasets["pr_detail"]["records"], repo_filter_normalized)
    issue_detail_records = filter_by_repo(datasets["issue_detail"]["records"], repo_filter_normalized)

    repo_counter = Counter(record.get("repo", "Unknown") for record in merged_records)
    top_repos = repo_counter.most_common(10)
    time_series_counter: Dict[str, int] = defaultdict(int)
    for record in merged_records:
        parsed = parse_datetime(record.get("created_at", ""))
        if parsed:
            time_series_counter[parsed.date().isoformat()] += 1

    closing_issue_counts: Dict[str, int] = defaultdict(int)
    for record in pr_issue_records:
        repo = record.get("repo", "Unknown")
        if record.get("closing_issue") is not None:
            closing_issue_counts[repo] += 1

    pr_month_counts: Dict[str, int] = defaultdict(int)
    for record in pr_detail_records:
        parsed = parse_datetime(record.get("created_at", ""))
        if parsed:
            key = parsed.strftime("%Y-%m")
            pr_month_counts[key] += 1

    label_counts: Counter[str] = Counter()
    for record in issue_detail_records:
        labels = record.get("labels", [])
        if isinstance(labels, list):
            for label in labels:
                if isinstance(label, dict):
                    name = label.get("name")
                else:
                    name = str(label)
                if name:
                    label_counts[name] += 1

    return {
        "top_repos": {
            "labels": [item[0] for item in top_repos],
            "values": [item[1] for item in top_repos],
        },
        "time_series": {
            "labels": sorted(time_series_counter.keys()),
            "values": [time_series_counter[key] for key in sorted(time_series_counter.keys())],
        },
        "closing_issue_distribution": {
            "labels": list(closing_issue_counts.keys()),
            "values": list(closing_issue_counts.values()),
        },
        "pr_month_histogram": {
            "labels": sorted(pr_month_counts.keys()),
            "values": [pr_month_counts[key] for key in sorted(pr_month_counts.keys())],
        },
        "top_labels": {
            "labels": [item[0] for item in label_counts.most_common(10)],
            "values": [item[1] for item in label_counts.most_common(10)],
        },
    }


@app.route("/visualize")
def visualize():
    repo_filter = request.args.get("repo")
    visualization_data = compute_visualization_data(repo_filter)
    return render_template(
        "visualize.html",
        repo_filter=repo_filter or "",
        visualization_data=visualization_data,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    dataset = get_dataset_or_404(dataset_name)
    repo_filter = request.args.get("repo")
    records = filter_by_repo(dataset["records"], repo_filter)
    return jsonify(records)


if __name__ == "__main__":
    app.run(debug=True)
