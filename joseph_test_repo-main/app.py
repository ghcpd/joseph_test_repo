import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, abort, jsonify, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

DATASET_CONFIG: Dict[str, Dict[str, Any]] = {
    "pr_issue": {
        "path": BASE_DIR / "input_data" / "pr_issue_single.jsonl",
        "key_field": "id",
        "title": "PR Issue Search Results",
        "display_fields": None,
    },
    "pr_detail": {
        "path": BASE_DIR / "input_data" / "pr_detail.jsonl",
        "key_field": "id",
        "title": "Pull Request Details",
        "display_fields": None,
    },
    "issue_detail": {
        "path": BASE_DIR / "input_data" / "issue_detail.jsonl",
        "key_field": "id",
        "title": "Issue Details",
        "display_fields": None,
    },
    "merged_data": {
        "path": BASE_DIR / "output_data" / "merged_data.jsonl",
        "key_field": "id",
        "title": "Merged PR-Issue Data",
        "display_fields": [
            "repo",
            "issue_number",
            "issue_title",
            "pull_number",
            "created_at",
        ],
    },
}

DATASETS: Dict[str, Dict[str, Any]] = {}
AGGREGATION_CACHE: Dict[str, Dict[str, Any]] = {}
RELATIONSHIPS: Dict[str, Dict[Any, Any]] = {
    "pr_by_repo_number": {},
    "issue_by_repo_number": {},
    "merged_by_repo_issue": defaultdict(list),
    "merged_by_repo_pr": defaultdict(list),
    "pr_issue_by_repo_pr": defaultdict(list),
}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def determine_display_fields(records: List[Dict[str, Any]]) -> List[str]:
    if not records:
        return []
    ordered = list(records[0].keys())
    return ordered


def initialize_datasets() -> None:
    for name, config in DATASET_CONFIG.items():
        records = load_jsonl(config["path"])
        key_field = config.get("key_field", "id")
        display_fields = config.get("display_fields")
        if display_fields is None:
            display_fields = determine_display_fields(records)
            config["display_fields"] = display_fields

        indexed = {}
        for record in records:
            key_value = record.get(key_field)
            if key_value is None:
                continue
            indexed[str(key_value)] = record

        DATASETS[name] = {
            "records": records,
            "index": indexed,
            "config": config,
            "count": len(records),
        }

    build_relationships()



def build_relationships() -> None:
    RELATIONSHIPS["merged_by_repo_issue"].clear()
    RELATIONSHIPS["merged_by_repo_pr"].clear()
    RELATIONSHIPS["pr_issue_by_repo_pr"].clear()
    RELATIONSHIPS["pr_by_repo_number"] = {}
    RELATIONSHIPS["issue_by_repo_number"] = {}

    def repo_key(repo: Optional[str], number: Any) -> Optional[Tuple[str, str]]:
        if repo is None or number is None:
            return None
        return repo.lower(), str(number)

    for record in DATASETS.get("pr_detail", {}).get("records", []):
        key = repo_key(record.get("repo"), record.get("number"))
        if key:
            RELATIONSHIPS["pr_by_repo_number"][key] = record

    for record in DATASETS.get("issue_detail", {}).get("records", []):
        key = repo_key(record.get("repo"), record.get("number"))
        if key:
            RELATIONSHIPS["issue_by_repo_number"][key] = record

    for record in DATASETS.get("merged_data", {}).get("records", []):
        repo = record.get("repo")
        if repo is None:
            continue
        issue_key = repo_key(repo, record.get("issue_number"))
        if issue_key:
            RELATIONSHIPS["merged_by_repo_issue"][issue_key].append(record)
        pr_key = repo_key(repo, record.get("pull_number"))
        if pr_key:
            RELATIONSHIPS["merged_by_repo_pr"][pr_key].append(record)

    for record in DATASETS.get("pr_issue", {}).get("records", []):
        key = repo_key(record.get("repo"), record.get("pull_number"))
        if key:
            RELATIONSHIPS["pr_issue_by_repo_pr"][key].append(record)


initialize_datasets()


@app.context_processor
def inject_globals() -> Dict[str, Any]:
    summary = {
        name: DATASETS[name]["count"] for name in DATASETS
    }
    return {
        "dataset_config": DATASET_CONFIG,
        "dataset_summary": summary,
    }


def parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_filtered_records(dataset_name: str, repo_filter: Optional[str]) -> List[Dict[str, Any]]:
    records = DATASETS.get(dataset_name, {}).get("records", [])
    if not repo_filter:
        return records
    repo_filter = repo_filter.lower()
    filtered: List[Dict[str, Any]] = []
    for record in records:
        repo = str(record.get("repo", ""))
        if repo.lower() == repo_filter:
            filtered.append(record)
    return filtered


def aggregate_merged_data(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    repo_counts = Counter()
    timeline: Dict[str, int] = defaultdict(int)
    for record in records:
        repo = record.get("repo", "Unknown")
        repo_counts[repo] += 1
        created = parse_iso_date(record.get("created_at"))
        if created:
            key = created.strftime("%Y-%m-%d")
            timeline[key] += 1
    top_repos = [
        {"repo": repo, "count": count} for repo, count in repo_counts.most_common(10)
    ]
    timeline_series = [
        {"date": date, "count": timeline[date]}
        for date in sorted(timeline.keys())
    ]
    return {
        "top_repos": top_repos,
        "timeline": timeline_series,
    }


def aggregate_pr_issue(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    distribution = []
    repo_counts: Dict[str, List[int]] = defaultdict(list)
    for record in records:
        repo = record.get("repo", "Unknown")
        closing = record.get("closing_issue") or []
        repo_counts[repo].append(len(closing))
    for repo, counts in repo_counts.items():
        distribution.append({"repo": repo, "closing_count": sum(counts)})
    distribution.sort(key=lambda x: x["closing_count"], reverse=True)
    return {"closing_distribution": distribution}


def aggregate_pr_detail(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    histogram: Dict[str, int] = defaultdict(int)
    for record in records:
        created = parse_iso_date(record.get("created_at"))
        if created:
            key = created.strftime("%Y-%m")
            histogram[key] += 1
    histogram_series = [
        {"month": month, "count": histogram[month]}
        for month in sorted(histogram.keys())
    ]
    return {"monthly_histogram": histogram_series}


def aggregate_issue_detail(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    label_counter = Counter()
    for record in records:
        labels = record.get("labels") or []
        for label in labels:
            name = label if isinstance(label, str) else label.get("name")
            if name:
                label_counter[str(name)] += 1
    top_labels = [
        {"label": label, "count": count}
        for label, count in label_counter.most_common(10)
    ]
    return {"top_labels": top_labels}


AGGREGATION_FUNCTIONS = {
    "merged_data": aggregate_merged_data,
    "pr_issue": aggregate_pr_issue,
    "pr_detail": aggregate_pr_detail,
    "issue_detail": aggregate_issue_detail,
}


def get_cached_aggregations(dataset_name: str, records: List[Dict[str, Any]], repo_filter: Optional[str]) -> Dict[str, Any]:
    cache_key = (dataset_name, repo_filter or "*")
    dataset_cache = AGGREGATION_CACHE.setdefault(dataset_name, {})
    if cache_key in dataset_cache:
        return dataset_cache[cache_key]
    aggregation_fn = AGGREGATION_FUNCTIONS.get(dataset_name)
    if aggregation_fn is None:
        dataset_cache[cache_key] = {}
        return {}
    result = aggregation_fn(records)
    dataset_cache[cache_key] = result
    return result


@app.route("/")
def index() -> Any:
    selected_dataset = request.args.get("dataset", "merged_data")
    if selected_dataset not in DATASETS:
        selected_dataset = "merged_data"
    repo_filter = request.args.get("repo")
    dataset_meta = {
        name: {
            "display_fields": config.get("display_fields", []),
            "key_field": config.get("key_field", "id"),
            "title": config.get("title", name),
        }
        for name, config in DATASET_CONFIG.items()
    }
    return render_template(
        "index.html",
        selected_dataset=selected_dataset,
        repo_filter=repo_filter,
        dataset_meta=dataset_meta,
    )


def build_related_items(dataset_name: str, record: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    related: Dict[str, List[Dict[str, Any]]] = {
        "merged_data": [],
        "pr_detail": [],
        "issue_detail": [],
        "pr_issue": [],
    }

    def add_related(target_dataset: str, candidate: Dict[str, Any]) -> None:
        target_config = DATASET_CONFIG.get(target_dataset, {})
        key_field = target_config.get("key_field", "id")
        key_value = candidate.get(key_field)
        if key_value is None:
            return
        related[target_dataset].append(
            {
                "record": candidate,
                "record_id": key_value,
                "dataset": target_dataset,
            }
        )

    repo = record.get("repo")
    repo_lower = repo.lower() if isinstance(repo, str) else None

    def repo_key(target_repo: Optional[str], number: Any) -> Optional[Tuple[str, str]]:
        if target_repo is None or number is None:
            return None
        return target_repo.lower(), str(number)

    key_field = DATASET_CONFIG.get(dataset_name, {}).get("key_field", "id")
    if dataset_name == "merged_data":
        issue_key = repo_key(repo, record.get("issue_number"))
        if issue_key:
            issue_record = RELATIONSHIPS["issue_by_repo_number"].get(issue_key)
            if issue_record:
                add_related("issue_detail", issue_record)
        pr_key = repo_key(repo, record.get("pull_number"))
        if pr_key:
            pr_record = RELATIONSHIPS["pr_by_repo_number"].get(pr_key)
            if pr_record:
                add_related("pr_detail", pr_record)
        if pr_key:
            for candidate in RELATIONSHIPS["pr_issue_by_repo_pr"].get(pr_key, []):
                add_related("pr_issue", candidate)
    elif dataset_name == "pr_detail":
        current_key = repo_key(repo, record.get("number"))
        if current_key:
            for candidate in RELATIONSHIPS["merged_by_repo_pr"].get(current_key, []):
                add_related("merged_data", candidate)
            for candidate in RELATIONSHIPS["pr_issue_by_repo_pr"].get(current_key, []):
                add_related("pr_issue", candidate)
        for issue_number in record.get("related_issues", []):
            issue_record = RELATIONSHIPS["issue_by_repo_number"].get(repo_key(repo, issue_number))
            if issue_record:
                add_related("issue_detail", issue_record)
    elif dataset_name == "issue_detail":
        for pull_number in record.get("pull_requests", []):
            pr_record = RELATIONSHIPS["pr_by_repo_number"].get(repo_key(repo, pull_number))
            if pr_record:
                add_related("pr_detail", pr_record)
            for merged_record in RELATIONSHIPS["merged_by_repo_pr"].get(repo_key(repo, pull_number), []):
                add_related("merged_data", merged_record)
        issue_key = repo_key(repo, record.get("number"))
        if issue_key:
            # Link to pr_issue via merged data relationships
            for merged_record in RELATIONSHIPS["merged_by_repo_issue"].get(issue_key, []):
                for pr_candidate in RELATIONSHIPS["pr_issue_by_repo_pr"].get(
                    repo_key(repo, merged_record.get("pull_number")), []
                ):
                    add_related("pr_issue", pr_candidate)
    else:  # pr_issue
        pr_key = repo_key(repo, record.get("pull_number"))
        if pr_key:
            for candidate in RELATIONSHIPS["merged_by_repo_pr"].get(pr_key, []):
                add_related("merged_data", candidate)
            pr_record = RELATIONSHIPS["pr_by_repo_number"].get(pr_key)
            if pr_record:
                add_related("pr_detail", pr_record)
        for issue_number in record.get("issue_numbers", []):
            issue_record = RELATIONSHIPS["issue_by_repo_number"].get(repo_key(repo, issue_number))
            if issue_record:
                add_related("issue_detail", issue_record)

    for dataset_items in related.values():
        dataset_items.sort(key=lambda item: str(item.get("record_id")))
    return related


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str) -> Any:
    dataset = DATASETS.get(dataset_name)
    if not dataset:
        abort(404)
    record = dataset["index"].get(str(record_id))
    if not record:
        abort(404)
    related_records = build_related_items(dataset_name, record)
    return render_template(
        "detail.html",
        dataset_name=dataset_name,
        record=record,
        related_records=related_records,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str) -> Any:
    if dataset_name not in DATASETS:
        abort(404)
    repo_filter = request.args.get("repo")
    records = get_filtered_records(dataset_name, repo_filter)
    aggregations = get_cached_aggregations(dataset_name, records, repo_filter)
    config = DATASET_CONFIG[dataset_name]
    return jsonify(
        {
            "data": records,
            "fields": config.get("display_fields", []),
            "count": len(records),
            "aggregations": aggregations,
        }
    )


@app.route("/visualize")
def visualize() -> Any:
    repo_filter = request.args.get("repo")
    return render_template("visualize.html", repo_filter=repo_filter)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
