import json
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from flask import Flask, abort, jsonify, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = Flask(__name__)


def parse_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def build_columns(records: List[Dict[str, Any]], default_columns: Optional[List[str]] = None) -> List[str]:
    if default_columns:
        return default_columns
    seen: set[str] = set()
    columns: List[str] = []
    for record in records:
        for key in record.keys():
            if key == "_id":
                continue
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def safe_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Remove Z suffix for ISO parsing if present.
        if value.endswith("Z"):
            value = value[:-1]
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class Dataset:
    def __init__(
        self,
        name: str,
        title: str,
        path: Path,
        id_getter: Callable[[Dict[str, Any]], str],
        display_columns: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.title = title
        self.path = path
        self.id_getter = id_getter
        self.display_columns = display_columns
        self.records: List[Dict[str, Any]] = []
        self.index: Dict[str, Dict[str, Any]] = {}

    def load(self) -> None:
        raw_records = parse_jsonl(self.path)
        self.records = []
        self.index = {}
        for record in raw_records:
            identifier = str(self.id_getter(record))
            record_copy = dict(record)
            record_copy["_id"] = identifier
            self.records.append(record_copy)
            self.index[identifier] = record_copy
        self.display_columns = build_columns(self.records, self.display_columns)


DATASET_CONFIG: Dict[str, Dataset] = {
    "pr_issue": Dataset(
        name="pr_issue",
        title="PR Issue Search Results",
        path=DATA_DIR / "input_data" / "pr_issue_single.jsonl",
        id_getter=lambda record: record.get("id")
        or f"{record.get('repo')}#{record.get('pull_number')}",
    ),
    "pr_detail": Dataset(
        name="pr_detail",
        title="Pull Request Details",
        path=DATA_DIR / "input_data" / "pr_detail.jsonl",
        id_getter=lambda record: record.get("id")
        or f"{record.get('repo')}#{record.get('number')}",
    ),
    "issue_detail": Dataset(
        name="issue_detail",
        title="Issue Details",
        path=DATA_DIR / "input_data" / "issue_detail.jsonl",
        id_getter=lambda record: record.get("id")
        or f"{record.get('repo')}#{record.get('number')}",
    ),
    "merged_data": Dataset(
        name="merged_data",
        title="Merged PR and Issue Data",
        path=DATA_DIR / "output_data" / "merged_data.jsonl",
        id_getter=lambda record: f"{record.get('repo')}#PR{record.get('pull_number')}#ISSUE{record.get('issue_number')}",
        display_columns=["repo", "issue_number", "issue_title", "pull_number", "created_at"],
    ),
}


def load_all_datasets() -> None:
    for dataset in DATASET_CONFIG.values():
        dataset.load()


load_all_datasets()


@lru_cache(maxsize=32)
def get_cached_aggregations(dataset_name: str, repo_filter: Optional[str] = None) -> Dict[str, Any]:
    repo_filter = repo_filter or "__all__"
    dataset = DATASET_CONFIG.get(dataset_name)
    if not dataset:
        return {}

    filtered_records = dataset.records
    if repo_filter != "__all__":
        filtered_records = [
            item
            for item in dataset.records
            if str(item.get("repo")) == repo_filter
        ]

    results: Dict[str, Any] = {}

    if dataset_name == "merged_data":
        repo_counts = Counter(item.get("repo") for item in filtered_records)
        top_repos = repo_counts.most_common(10)
        results["top_repos"] = {
            "labels": [repo for repo, _ in top_repos],
            "values": [count for _, count in top_repos],
        }

        timeline: Dict[str, int] = defaultdict(int)
        for item in filtered_records:
            created = safe_datetime(item.get("created_at"))
            if created:
                key = created.strftime("%Y-%m-%d")
                timeline[key] += 1
        sorted_timeline = sorted(timeline.items())
        results["timeline"] = {
            "dates": [entry[0] for entry in sorted_timeline],
            "counts": [entry[1] for entry in sorted_timeline],
        }

    elif dataset_name == "pr_issue":
        closing_counter: Dict[str, int] = defaultdict(int)
        for item in filtered_records:
            repo = item.get("repo", "Unknown")
            if item.get("closing_issue"):
                closing_counter[str(repo)] += 1
        sorted_counts = sorted(closing_counter.items(), key=lambda pair: pair[1], reverse=True)[:10]
        results["closing_issue_distribution"] = {
            "labels": [pair[0] for pair in sorted_counts],
            "values": [pair[1] for pair in sorted_counts],
        }

    elif dataset_name == "pr_detail":
        monthly_counter: Dict[str, int] = defaultdict(int)
        for item in filtered_records:
            created = safe_datetime(item.get("created_at"))
            if created:
                key = created.strftime("%Y-%m")
                monthly_counter[key] += 1
        sorted_months = sorted(monthly_counter.items())
        results["monthly_histogram"] = {
            "labels": [pair[0] for pair in sorted_months],
            "values": [pair[1] for pair in sorted_months],
        }

    elif dataset_name == "issue_detail":
        label_counts = Counter()
        for item in filtered_records:
            labels = item.get("labels") or []
            for label in labels:
                label_counts[str(label)] += 1
        top_labels = label_counts.most_common(10)
        results["top_labels"] = {
            "labels": [pair[0] for pair in top_labels],
            "values": [pair[1] for pair in top_labels],
        }

    return results


def get_dataset_or_404(dataset_name: str) -> Dataset:
    dataset = DATASET_CONFIG.get(dataset_name)
    if not dataset:
        abort(404, f"Dataset '{dataset_name}' not found")
    return dataset


def build_related_links(dataset_name: str, record: Dict[str, Any]) -> List[Dict[str, Any]]:
    related: List[Dict[str, Any]] = []

    if dataset_name == "pr_detail":
        repo = record.get("repo")
        linked_issue = record.get("linked_issue")
        if repo and linked_issue is not None:
            issue_id = f"{repo}#{linked_issue}"
            issue_record = DATASET_CONFIG["issue_detail"].index.get(issue_id)
            if issue_record:
                related.append(
                    {
                        "label": "Linked Issue",
                        "dataset": "issue_detail",
                        "record": issue_record,
                        "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_record["_id"]),
                    }
                )
        pr_issue_record = DATASET_CONFIG["pr_issue"].index.get(record["_id"])
        if pr_issue_record:
            related.append(
                {
                    "label": "PR Search Entry",
                    "dataset": "pr_issue",
                    "record": pr_issue_record,
                    "url": url_for("dataset_detail", dataset_name="pr_issue", record_id=pr_issue_record["_id"]),
                }
            )

    elif dataset_name == "issue_detail":
        repo = record.get("repo")
        issue_number = record.get("number")
        if repo and issue_number is not None:
            pr_matches = [
                pr_record
                for pr_record in DATASET_CONFIG["pr_detail"].records
                if pr_record.get("repo") == repo and pr_record.get("linked_issue") == issue_number
            ]
            for pr_record in pr_matches:
                related.append(
                    {
                        "label": "Linked Pull Request",
                        "dataset": "pr_detail",
                        "record": pr_record,
                        "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_record["_id"]),
                    }
                )
        for pr_record in DATASET_CONFIG["pr_issue"].records:
            closing_issue = pr_record.get("closing_issue")
            if closing_issue and closing_issue.get("issue_number") == issue_number and pr_record.get("repo") == repo:
                related.append(
                    {
                        "label": "Closing PR Candidate",
                        "dataset": "pr_issue",
                        "record": pr_record,
                        "url": url_for("dataset_detail", dataset_name="pr_issue", record_id=pr_record["_id"]),
                    }
                )

    elif dataset_name == "merged_data":
        repo = record.get("repo")
        pull_number = record.get("pull_number")
        issue_number = record.get("issue_number")
        if repo is not None and pull_number is not None:
            pr_id = f"{repo}#{pull_number}"
            pr_record = DATASET_CONFIG["pr_detail"].index.get(pr_id)
            if pr_record:
                related.append(
                    {
                        "label": "Pull Request Detail",
                        "dataset": "pr_detail",
                        "record": pr_record,
                        "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_record["_id"]),
                    }
                )
            pr_issue_record = DATASET_CONFIG["pr_issue"].index.get(pr_id)
            if pr_issue_record:
                related.append(
                    {
                        "label": "Search Result Entry",
                        "dataset": "pr_issue",
                        "record": pr_issue_record,
                        "url": url_for("dataset_detail", dataset_name="pr_issue", record_id=pr_issue_record["_id"]),
                    }
                )
        if repo is not None and issue_number is not None:
            issue_id = f"{repo}#{issue_number}"
            issue_record = DATASET_CONFIG["issue_detail"].index.get(issue_id)
            if issue_record:
                related.append(
                    {
                        "label": "Issue Detail",
                        "dataset": "issue_detail",
                        "record": issue_record,
                        "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_record["_id"]),
                    }
                )

    elif dataset_name == "pr_issue":
        repo = record.get("repo")
        pull_number = record.get("pull_number")
        closing_issue = record.get("closing_issue") or {}
        issue_number = closing_issue.get("issue_number")
        if repo is not None and pull_number is not None:
            pr_id = f"{repo}#{pull_number}"
            pr_record = DATASET_CONFIG["pr_detail"].index.get(pr_id)
            if pr_record:
                related.append(
                    {
                        "label": "Pull Request Detail",
                        "dataset": "pr_detail",
                        "record": pr_record,
                        "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_record["_id"]),
                    }
                )
        if repo is not None and issue_number is not None:
            issue_id = f"{repo}#{issue_number}"
            issue_record = DATASET_CONFIG["issue_detail"].index.get(issue_id)
            if issue_record:
                related.append(
                    {
                        "label": "Linked Issue Detail",
                        "dataset": "issue_detail",
                        "record": issue_record,
                        "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_record["_id"]),
                    }
                )

    return related


@app.route("/")
def index() -> str:
    selected_dataset = request.args.get("dataset", "merged_data")
    dataset = DATASET_CONFIG.get(selected_dataset)
    if not dataset:
        selected_dataset = "merged_data"
        dataset = DATASET_CONFIG[selected_dataset]

    summary = {
        name: len(info.records)
        for name, info in DATASET_CONFIG.items()
    }

    return render_template(
        "index.html",
        datasets=DATASET_CONFIG,
        selected_dataset=selected_dataset,
        summary=summary,
        table_columns=dataset.display_columns,
        table_records=dataset.records,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str) -> str:
    dataset = get_dataset_or_404(dataset_name)
    record = dataset.index.get(record_id)
    if not record:
        abort(404, "Record not found")

    related = build_related_links(dataset_name, record)

    return render_template(
        "detail.html",
        dataset=dataset,
        record=record,
        related=related,
    )


@app.route("/visualize")
def visualize() -> str:
    repo_filter = request.args.get("repo")

    merged_data_agg = get_cached_aggregations("merged_data", repo_filter)
    pr_issue_agg = get_cached_aggregations("pr_issue", repo_filter)
    pr_detail_agg = get_cached_aggregations("pr_detail", repo_filter)
    issue_detail_agg = get_cached_aggregations("issue_detail", repo_filter)

    repo_options = sorted(
        {
            str(record.get("repo"))
            for dataset in DATASET_CONFIG.values()
            for record in dataset.records
            if record.get("repo")
        }
    )

    return render_template(
        "visualize.html",
        repo_filter=repo_filter,
        repo_options=repo_options,
        merged_data=merged_data_agg,
        pr_issue=pr_issue_agg,
        pr_detail=pr_detail_agg,
        issue_detail=issue_detail_agg,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    dataset = get_dataset_or_404(dataset_name)
    repo_filter = request.args.get("repo")
    records = dataset.records
    if repo_filter:
        records = [record for record in records if str(record.get("repo")) == repo_filter]

    aggregations = get_cached_aggregations(dataset_name, repo_filter)
    return jsonify({"records": records, "aggregations": aggregations})


@app.template_filter("display_value")
def display_value(value: Any) -> str:
    if isinstance(value, dict) or isinstance(value, list):
        return json.dumps(value, indent=2)
    if value is None:
        return "N/A"
    return str(value)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
