from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from flask import Flask, abort, jsonify, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = Flask(__name__)
app.config.update(JSON_SORT_KEYS=False)

DatasetRecord = Dict[str, Any]


DATASET_CONFIG: Dict[str, Dict[str, Any]] = {
    "pr_issue": {
        "path": DATA_DIR / "input_data" / "pr_issue_single.jsonl",
        "id_getter": lambda record: str(record.get("id") or record.get("number")),
    },
    "pr_detail": {
        "path": DATA_DIR / "input_data" / "pr_detail.jsonl",
        "id_getter": lambda record: str(record.get("id") or record.get("number")),
    },
    "issue_detail": {
        "path": DATA_DIR / "input_data" / "issue_detail.jsonl",
        "id_getter": lambda record: str(record.get("id") or record.get("number")),
    },
    "merged_data": {
        "path": DATA_DIR / "output_data" / "merged_data.jsonl",
        "id_getter": lambda record: "{}:{}:{}".format(
            (record.get("repo", "unknown") or "unknown").replace("/", "__"),
            record.get("pull_number", "n/a"),
            record.get("issue_number", "n/a"),
        ),
    },
}


def load_jsonl(path: Path) -> List[DatasetRecord]:
    if not path.exists():
        return []
    records: List[DatasetRecord] = []
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


def extract_repo(record: DatasetRecord, dataset_name: str) -> str:
    if dataset_name == "pr_issue":
        repository_url = record.get("repository_url") or ""
        if "repos/" in repository_url:
            return repository_url.split("repos/")[-1]
        return repository_url.split("https://github.com/")[-1]
    if dataset_name == "pr_detail":
        base = record.get("base") or {}
        repo = base.get("repo") or {}
        return repo.get("full_name") or record.get("repository", "")
    if dataset_name == "issue_detail":
        return record.get("repository") or record.get("repo", "")
    if dataset_name == "merged_data":
        return record.get("repo", "")
    return ""


def initialize_datasets() -> Tuple[Dict[str, Dict[str, DatasetRecord]], Dict[str, List[DatasetRecord]]]:
    dataset_indexes: Dict[str, Dict[str, DatasetRecord]] = {}
    dataset_records: Dict[str, List[DatasetRecord]] = {}

    for name, config in DATASET_CONFIG.items():
        records = load_jsonl(config["path"])
        index: Dict[str, DatasetRecord] = {}
        id_getter: Callable[[DatasetRecord], str] = config.get("id_getter", lambda record: str(record.get("id")))
        for raw_record in records:
            record = dict(raw_record)
            record_id = id_getter(record) or str(len(index))
            record["_record_id"] = record_id
            record["_repo"] = extract_repo(record, name) or "Unknown"
            index[record_id] = record
        dataset_indexes[name] = index
        dataset_records[name] = list(index.values())

    return dataset_indexes, dataset_records


data_indexes, datasets = initialize_datasets()


def available_repositories() -> List[str]:
    repos = set()
    for records in datasets.values():
        for record in records:
            repo_name = record.get("_repo")
            if repo_name:
                repos.add(repo_name)
    return sorted(repos)


MERGED_PR_INDEX: Dict[Tuple[str, Any], List[DatasetRecord]] = defaultdict(list)
MERGED_ISSUE_INDEX: Dict[Tuple[str, Any], List[DatasetRecord]] = defaultdict(list)
PR_INDEX: Dict[Tuple[str, Any], DatasetRecord] = {}
ISSUE_INDEX: Dict[Tuple[str, Any], DatasetRecord] = {}


for record in datasets.get("merged_data", []):
    repo = record.get("_repo")
    MERGED_PR_INDEX[(repo, record.get("pull_number"))].append(record)
    MERGED_ISSUE_INDEX[(repo, record.get("issue_number"))].append(record)

for record in datasets.get("pr_detail", []):
    PR_INDEX[(record.get("_repo"), record.get("number"))] = record

for record in datasets.get("issue_detail", []):
    ISSUE_INDEX[(record.get("_repo"), record.get("number"))] = record


@app.template_filter("format_value")
def format_value(value: Any) -> str:
    if value in (None, ""):
        return "N/A"
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)


def get_display_fields(dataset_name: str) -> List[str]:
    if dataset_name == "merged_data":
        return ["repo", "issue_number", "issue_title", "pull_number", "created_at"]
    records = datasets.get(dataset_name, [])
    if not records:
        return []
    record = records[0]
    keys = [key for key in record.keys() if not key.startswith("_")]
    return keys


def get_summary_counts() -> Dict[str, int]:
    return {name: len(records) for name, records in datasets.items()}


def filter_dataset(dataset_name: str, repo_filter: Optional[str] = None) -> List[DatasetRecord]:
    records = datasets.get(dataset_name, [])
    if repo_filter:
        repo_filter = repo_filter.lower()
        filtered = [record for record in records if (record.get("_repo") or "").lower() == repo_filter]
        return filtered
    return records


def parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


aggregation_cache: Dict[Tuple[str, str, Optional[str]], Any] = {}


def cached_aggregation(dataset_name: str, aggregation: str, repo_filter: Optional[str], calculator: Callable[[], Any]) -> Any:
    cache_key = (dataset_name, aggregation, repo_filter or "*")
    if cache_key not in aggregation_cache:
        aggregation_cache[cache_key] = calculator()
    return aggregation_cache[cache_key]


def merged_repo_counts(repo_filter: Optional[str] = None) -> Dict[str, Any]:
    def compute() -> Dict[str, Any]:
        records = filter_dataset("merged_data", repo_filter)
        counter = Counter(record.get("_repo") or "Unknown" for record in records)
        most_common = counter.most_common(10)
        return {
            "labels": [item[0] for item in most_common],
            "values": [item[1] for item in most_common],
        }

    return cached_aggregation("merged_data", "repo_counts", repo_filter, compute)


def merged_timeline(repo_filter: Optional[str] = None) -> Dict[str, Any]:
    def compute() -> Dict[str, Any]:
        records = filter_dataset("merged_data", repo_filter)
        timeline_counter: Dict[str, int] = defaultdict(int)
        for record in records:
            created_at = record.get("created_at")
            parsed = parse_date(created_at)
            if parsed:
                timeline_counter[parsed.date().isoformat()] += 1
        sorted_items = sorted(timeline_counter.items())
        return {
            "labels": [item[0] for item in sorted_items],
            "values": [item[1] for item in sorted_items],
        }

    return cached_aggregation("merged_data", "timeline", repo_filter, compute)


def closing_issue_distribution(repo_filter: Optional[str] = None) -> Dict[str, Any]:
    def compute() -> Dict[str, Any]:
        records = filter_dataset("pr_issue", repo_filter)
        repo_counter: Dict[str, int] = defaultdict(int)
        for record in records:
            repo_counter[record.get("_repo") or "Unknown"] += 1
        sorted_items = sorted(repo_counter.items(), key=lambda item: (-item[1], item[0]))
        return {
            "labels": [item[0] for item in sorted_items],
            "values": [item[1] for item in sorted_items],
        }

    return cached_aggregation("pr_issue", "closing_issue", repo_filter, compute)


def pr_monthly_histogram(repo_filter: Optional[str] = None) -> Dict[str, Any]:
    def compute() -> Dict[str, Any]:
        records = filter_dataset("pr_detail", repo_filter)
        month_counter: Dict[str, int] = defaultdict(int)
        for record in records:
            created_at = record.get("created_at")
            parsed = parse_date(created_at)
            if parsed:
                month_label = parsed.strftime("%Y-%m")
                month_counter[month_label] += 1
        sorted_items = sorted(month_counter.items())
        return {
            "labels": [item[0] for item in sorted_items],
            "values": [item[1] for item in sorted_items],
        }

    return cached_aggregation("pr_detail", "monthly_counts", repo_filter, compute)


def issue_label_counts(repo_filter: Optional[str] = None) -> Dict[str, Any]:
    def compute() -> Dict[str, Any]:
        records = filter_dataset("issue_detail", repo_filter)
        label_counter: Dict[str, int] = defaultdict(int)
        for record in records:
            labels = record.get("labels") or []
            for label in labels:
                if isinstance(label, dict):
                    name = label.get("name")
                else:
                    name = label
                if name:
                    label_counter[str(name)] += 1
        most_common = sorted(label_counter.items(), key=lambda item: (-item[1], item[0]))[:10]
        return {
            "labels": [item[0] for item in most_common],
            "values": [item[1] for item in most_common],
        }

    return cached_aggregation("issue_detail", "label_counts", repo_filter, compute)


def get_related_records(dataset_name: str, record: DatasetRecord) -> List[Dict[str, str]]:
    related: List[Dict[str, str]] = []
    repo = record.get("_repo")
    if dataset_name == "pr_detail":
        merged_entries = MERGED_PR_INDEX.get((repo, record.get("number")), [])
        issue_ids = set()
        for merged in merged_entries:
            issue_key = (repo, merged.get("issue_number"))
            issue_record = ISSUE_INDEX.get(issue_key)
            if issue_record and issue_record.get("_record_id") not in issue_ids:
                issue_ids.add(issue_record["_record_id"])
                related.append(
                    {
                        "title": f"Issue #{issue_record.get('number')} - {issue_record.get('title')}",
                        "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_record["_record_id"]),
                    }
                )
    elif dataset_name == "issue_detail":
        merged_entries = MERGED_ISSUE_INDEX.get((repo, record.get("number")), [])
        pr_ids = set()
        for merged in merged_entries:
            pr_key = (repo, merged.get("pull_number"))
            pr_record = PR_INDEX.get(pr_key)
            if pr_record and pr_record.get("_record_id") not in pr_ids:
                pr_ids.add(pr_record["_record_id"])
                related.append(
                    {
                        "title": f"PR #{pr_record.get('number')} - {pr_record.get('title')}",
                        "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_record["_record_id"]),
                    }
                )
    elif dataset_name == "merged_data":
        issue_key = (repo, record.get("issue_number"))
        pr_key = (repo, record.get("pull_number"))
        issue_record = ISSUE_INDEX.get(issue_key)
        pr_record = PR_INDEX.get(pr_key)
        if issue_record:
            related.append(
                {
                    "title": f"Source Issue #{issue_record.get('number')} - {issue_record.get('title')}",
                    "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_record["_record_id"]),
                }
            )
        if pr_record:
            related.append(
                {
                    "title": f"Source PR #{pr_record.get('number')} - {pr_record.get('title')}",
                    "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_record["_record_id"]),
                }
            )
    elif dataset_name == "pr_issue":
        closing_issue = record.get("closing_issue")
        pr_number = record.get("number")
        issue_key = (repo, closing_issue)
        pr_key = (repo, pr_number)
        issue_record = ISSUE_INDEX.get(issue_key)
        pr_record = PR_INDEX.get(pr_key)
        if issue_record:
            related.append(
                {
                    "title": f"Closing Issue #{issue_record.get('number')}",
                    "url": url_for("dataset_detail", dataset_name="issue_detail", record_id=issue_record["_record_id"]),
                }
            )
        if pr_record:
            related.append(
                {
                    "title": f"PR #{pr_record.get('number')} - {pr_record.get('title')}",
                    "url": url_for("dataset_detail", dataset_name="pr_detail", record_id=pr_record["_record_id"]),
                }
            )
    return related


@app.route("/")
def index():
    dataset_name = request.args.get("dataset", "merged_data")
    if dataset_name not in datasets:
        dataset_name = "merged_data"
    summary = get_summary_counts()
    records = datasets.get(dataset_name, [])
    fields = get_display_fields(dataset_name)
    return render_template(
        "index.html",
        datasets=datasets,
        summary=summary,
        selected_dataset=dataset_name,
        display_fields=fields,
        records=records,
        repositories=available_repositories(),
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str):
    if dataset_name not in data_indexes:
        abort(404)
    record = data_indexes[dataset_name].get(record_id)
    if not record:
        abort(404)
    items = [
        {
            "key": key,
            "value": value,
            "is_complex": isinstance(value, (dict, list)),
        }
        for key, value in record.items()
        if not key.startswith("_")
    ]
    related = get_related_records(dataset_name, record)
    return render_template(
        "detail.html",
        dataset_name=dataset_name,
        record_id=record_id,
        items=items,
        related=related,
    )


@app.route("/visualize")
def visualize():
    repo_filter = request.args.get("repo")
    return render_template(
        "visualize.html",
        repo_filter=repo_filter or "",
        repositories=available_repositories(),
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    if dataset_name not in datasets:
        abort(404)
    repo_filter = request.args.get("repo")
    aggregation = request.args.get("aggregation")
    if aggregation:
        if dataset_name == "merged_data":
            if aggregation == "repo_counts":
                result = merged_repo_counts(repo_filter)
            elif aggregation == "timeline":
                result = merged_timeline(repo_filter)
            else:
                abort(400)
        elif dataset_name == "pr_issue" and aggregation == "closing_issue":
            result = closing_issue_distribution(repo_filter)
        elif dataset_name == "pr_detail" and aggregation == "monthly_counts":
            result = pr_monthly_histogram(repo_filter)
        elif dataset_name == "issue_detail" and aggregation == "label_counts":
            result = issue_label_counts(repo_filter)
        else:
            abort(400)
        return jsonify(
            {
                "dataset": dataset_name,
                "aggregation": aggregation,
                "repo_filter": repo_filter,
                "data": result,
            }
        )
    filtered = filter_dataset(dataset_name, repo_filter)
    return jsonify(
        {
            "dataset": dataset_name,
            "repo_filter": repo_filter,
            "count": len(filtered),
            "data": filtered,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
