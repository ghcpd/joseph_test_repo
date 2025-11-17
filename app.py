import base64
import json
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from flask import Flask, abort, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent


def encode_identifier(raw: str) -> str:
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")
    return encoded.rstrip("=")


def decode_identifier(encoded: str) -> str:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode((encoded + padding).encode("utf-8")).decode("utf-8")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def is_scalar(value: Any) -> bool:
    return not isinstance(value, (dict, list))


def stringify(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value == "":
        return "N/A"
    return str(value)


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


class DataStore:
    DATASET_TITLES = {
        "merged_data": "Merged PR–Issue Data",
        "pr_issue": "PR Issue Search Results",
        "pr_detail": "Pull Request Details",
        "issue_detail": "Issue Details",
    }

    FILE_MAP = {
        "pr_issue": Path("data/input_data/pr_issue_single.jsonl"),
        "pr_detail": Path("data/input_data/pr_detail.jsonl"),
        "issue_detail": Path("data/input_data/issue_detail.jsonl"),
        "merged_data": Path("data/output_data/merged_data.jsonl"),
    }

    def __init__(self) -> None:
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self.summary_counts: Dict[str, int] = {}
        self.pr_to_issue_numbers: defaultdict[str, set] = defaultdict(set)
        self.issue_to_pr_numbers: defaultdict[str, set] = defaultdict(set)
        self._load_all()

    def _load_all(self) -> None:
        for dataset_name, relative_path in self.FILE_MAP.items():
            dataset_path = BASE_DIR / relative_path
            if not dataset_path.exists():
                raise FileNotFoundError(f"Missing dataset file: {dataset_path}")
            raw_records = load_jsonl(dataset_path)
            prepared = self._prepare_dataset(dataset_name, raw_records)
            self.datasets[dataset_name] = prepared
        self.summary_counts = {
            name: dataset["count"] for name, dataset in self.datasets.items()
        }
        self._build_relationships()

    def _prepare_dataset(
        self, dataset_name: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        dataset_records: Dict[str, Dict[str, Any]] = {}
        records_by_safe: Dict[str, Dict[str, Any]] = {}
        index_by_key: Dict[Tuple[str, str, int], List[Dict[str, Any]]] = defaultdict(list)
        columns = self._detect_columns(dataset_name, records)

        for position, record in enumerate(records):
            normalized = dict(record)
            record_id = self._create_record_id(dataset_name, normalized, position)
            safe_id = encode_identifier(record_id)
            link_keys = self._derive_link_keys(dataset_name, normalized)
            normalized["_record_id"] = record_id
            normalized["_safe_id"] = safe_id
            normalized["_link_keys"] = link_keys
            normalized["_dataset"] = dataset_name
            dataset_records[record_id] = normalized
            records_by_safe[safe_id] = normalized
            for key in link_keys:
                index_by_key[key].append(normalized)

        return {
            "records": dataset_records,
            "records_by_safe": records_by_safe,
            "columns": columns,
            "count": len(dataset_records),
            "index_by_key": dict(index_by_key),
        }

    def _detect_columns(
        self, dataset_name: str, records: List[Dict[str, Any]]
    ) -> List[str]:
        if dataset_name == "merged_data":
            return [
                "repo",
                "issue_number",
                "issue_title",
                "pull_number",
                "created_at",
            ]
        if not records:
            return []
        ordered_keys: List[str] = []
        for record in records:
            for key in record.keys():
                if key.startswith("_"):
                    continue
                if key not in ordered_keys:
                    ordered_keys.append(key)
        return ordered_keys

    def _create_record_id(
        self, dataset_name: str, record: Dict[str, Any], position: int
    ) -> str:
        repo = record.get("repo") or self._extract_repo_from_record(record)
        if dataset_name == "pr_detail":
            return f"{repo or 'unknown'}|pr|{record.get('number', position)}"
        if dataset_name == "issue_detail":
            return f"{repo or 'unknown'}|issue|{record.get('number', position)}"
        if dataset_name == "merged_data":
            return (
                f"{repo or 'unknown'}|merged|{record.get('pull_number', position)}|"
                f"{record.get('issue_number', position)}"
            )
        if dataset_name == "pr_issue":
            base = record.get("search_id") or record.get("id") or record.get("pull_number")
            return f"{repo or 'unknown'}|search|{base or position}"
        return f"{dataset_name}|{position}"

    def _derive_link_keys(
        self, dataset_name: str, record: Dict[str, Any]
    ) -> List[Tuple[str, str, int]]:
        keys: List[Tuple[str, str, int]] = []
        repo = record.get("repo") or self._extract_repo_from_record(record)
        if dataset_name in {"pr_detail", "pr_issue"}:
            number = record.get("number") if dataset_name == "pr_detail" else record.get("pull_number")
            if repo and isinstance(number, int):
                keys.append(("pr", repo, number))
        if dataset_name == "issue_detail":
            number = record.get("number")
            if repo and isinstance(number, int):
                keys.append(("issue", repo, number))
        if dataset_name == "merged_data":
            pull_number = record.get("pull_number")
            issue_number = record.get("issue_number")
            if repo and isinstance(pull_number, int):
                keys.append(("pr", repo, pull_number))
            if repo and isinstance(issue_number, int):
                keys.append(("issue", repo, issue_number))
        return keys

    def _extract_repo_from_record(self, record: Dict[str, Any]) -> Optional[str]:
        repo_url = record.get("repository_url")
        if isinstance(repo_url, str) and "/repos/" in repo_url:
            return repo_url.split("/repos/")[-1]
        return None

    def _build_relationships(self) -> None:
        for dataset_name, dataset in self.datasets.items():
            for record in dataset["records"].values():
                repo = record.get("repo") or self._extract_repo_from_record(record)
                if not repo:
                    continue
                if dataset_name == "pr_issue":
                    pr_number = record.get("pull_number")
                    if isinstance(pr_number, int):
                        issues = record.get("closing_issue") or []
                        for issue in issues:
                            issue_number = issue.get("issue_number") or issue.get("number")
                            if isinstance(issue_number, int):
                                self.pr_to_issue_numbers[(repo, pr_number)].add(issue_number)
                                self.issue_to_pr_numbers[(repo, issue_number)].add(pr_number)
                elif dataset_name == "issue_detail":
                    issue_number = record.get("number")
                    if isinstance(issue_number, int):
                        for pr_number in record.get("pull_requests") or []:
                            if isinstance(pr_number, int):
                                self.pr_to_issue_numbers[(repo, pr_number)].add(issue_number)
                                self.issue_to_pr_numbers[(repo, issue_number)].add(pr_number)
                elif dataset_name == "merged_data":
                    pr_number = record.get("pull_number")
                    issue_number = record.get("issue_number")
                    if isinstance(pr_number, int) and isinstance(issue_number, int):
                        self.pr_to_issue_numbers[(repo, pr_number)].add(issue_number)
                        self.issue_to_pr_numbers[(repo, issue_number)].add(pr_number)

    def available_datasets(self) -> List[str]:
        return list(self.datasets.keys())

    def get_dataset(self, dataset_name: str) -> Dict[str, Any]:
        dataset = self.datasets.get(dataset_name)
        if dataset is None:
            raise KeyError(dataset_name)
        return dataset

    def get_records(
        self, dataset_name: str, repo_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_name)
        records = list(dataset["records"].values())
        if repo_filter:
            repo_filter_lower = repo_filter.lower()
            filtered = [
                record
                for record in records
                if isinstance(record.get("repo"), str)
                and record["repo"].lower() == repo_filter_lower
            ]
            return filtered
        return records

    def get_record(self, dataset_name: str, safe_id: str) -> Optional[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_name)
        record = dataset["records_by_safe"].get(safe_id)
        if record:
            return record
        try:
            decoded = decode_identifier(safe_id)
        except Exception:  # pylint: disable=broad-except
            return None
        return dataset["records"].get(decoded)

    def flatten_record(
        self, record: Dict[str, Any], columns: Iterable[str]
    ) -> Dict[str, str]:
        flattened: Dict[str, str] = {}
        for column in columns:
            if column == "created_at" and "created_at" not in record:
                value = record.get("pull_created_at")
            else:
                value = record.get(column)
            if column == "closing_issue" and isinstance(value, list):
                value = [issue.get("issue_number") for issue in value]
            flattened[column] = stringify(value)
        return flattened

    def strip_internal(self, record: Dict[str, Any]) -> Dict[str, Any]:
        public = {}
        for key, value in record.items():
            if key.startswith("_"):
                continue
            public[key] = value
        return public

    def get_table_rows(
        self, dataset_name: str, repo_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_name)
        columns = dataset["columns"]
        rows = []
        for record in self.get_records(dataset_name, repo_filter):
            row = {
                "safe_id": record["_safe_id"],
                "values": self.flatten_record(record, columns),
            }
            rows.append(row)
        return rows

    def get_api_payload(
        self, dataset_name: str, repo_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        payload = []
        for record in self.get_records(dataset_name, repo_filter):
            payload.append(self.strip_internal(record))
        return payload

    def get_related(self, dataset_name: str, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        repo = record.get("repo") or self._extract_repo_from_record(record)
        sections: List[Dict[str, Any]] = []
        if not repo:
            return sections

        if dataset_name == "pr_detail":
            pr_number = record.get("number")
            issue_numbers = self.pr_to_issue_numbers.get((repo, pr_number), set())
            issues = [
                self._build_link("issue_detail", repo, issue_number)
                for issue_number in sorted(issue_numbers)
                if self._build_link("issue_detail", repo, issue_number)
            ]
            if issues:
                sections.append({"title": "Linked Issues", "items": issues})
            search_entries = [
                self._build_link_from_record(entry)
                for entry in self.get_dataset("pr_issue")["index_by_key"].get(("pr", repo, pr_number), [])
            ]
            if search_entries:
                sections.append(
                    {"title": "Search Matches", "items": search_entries}
                )
        elif dataset_name == "issue_detail":
            issue_number = record.get("number")
            pr_numbers = self.issue_to_pr_numbers.get((repo, issue_number), set())
            prs = [
                self._build_link("pr_detail", repo, pr_number)
                for pr_number in sorted(pr_numbers)
                if self._build_link("pr_detail", repo, pr_number)
            ]
            if prs:
                sections.append({"title": "Linked Pull Requests", "items": prs})
            merged_entries = [
                self._build_link_from_record(entry)
                for entry in self.get_dataset("merged_data")["index_by_key"].get(("issue", repo, issue_number), [])
            ]
            if merged_entries:
                sections.append({"title": "Merged Data Rows", "items": merged_entries})
        elif dataset_name == "merged_data":
            pr_number = record.get("pull_number")
            issue_number = record.get("issue_number")
            pr_link = self._build_link("pr_detail", repo, pr_number)
            issue_link = self._build_link("issue_detail", repo, issue_number)
            extras: List[Dict[str, Any]] = []
            if pr_link:
                extras.append(pr_link)
            if issue_link:
                extras.append(issue_link)
            if extras:
                sections.append({"title": "Source Entries", "items": extras})
            search_matches = [
                self._build_link_from_record(entry)
                for entry in self.get_dataset("pr_issue")["index_by_key"].get(("pr", repo, pr_number), [])
            ]
            if search_matches:
                sections.append(
                    {"title": "Search Matches", "items": search_matches}
                )
        elif dataset_name == "pr_issue":
            pr_number = record.get("pull_number")
            pr_link = self._build_link("pr_detail", repo, pr_number)
            issue_links = []
            for issue in record.get("closing_issue") or []:
                issue_number = issue.get("issue_number") or issue.get("number")
                link = self._build_link("issue_detail", repo, issue_number)
                if link:
                    issue_links.append(link)
            extras: List[Dict[str, Any]] = []
            if pr_link:
                extras.append(pr_link)
            if extras:
                sections.append({"title": "Related Pull Request", "items": extras})
            if issue_links:
                sections.append({"title": "Closing Issues", "items": issue_links})
        return sections

    def _build_link(self, dataset_name: str, repo: str, number: Optional[int]) -> Optional[Dict[str, Any]]:
        if number is None:
            return None
        candidates = self.get_dataset(dataset_name)["index_by_key"].get(("pr" if dataset_name == "pr_detail" else "issue", repo, number))
        if not candidates:
            return None
        record = candidates[0]
        return self._build_link_from_record(record)

    def _build_link_from_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        dataset_name = record.get("_dataset", "")
        label: str
        if dataset_name == "pr_detail":
            label = f"PR #{record.get('number')} – {record.get('title', 'N/A')}"
        elif dataset_name == "issue_detail":
            label = f"Issue #{record.get('number')} – {record.get('title', 'N/A')}"
        elif dataset_name == "merged_data":
            label = (
                f"Merged #{record.get('pull_number')} ↔ #{record.get('issue_number')}"
            )
        else:
            label = record.get("repo", "Record")
        return {
            "dataset": dataset_name,
            "safe_id": record.get("_safe_id"),
            "label": label,
        }


store = DataStore()
app = Flask(__name__)


@app.template_filter("render_value")
def render_value(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value)


@app.route("/")
def index() -> str:
    dataset_name = request.args.get("dataset", "merged_data")
    repo_filter = request.args.get("repo")
    if dataset_name not in store.datasets:
        abort(404)
    dataset = store.get_dataset(dataset_name)
    table_rows = store.get_table_rows(dataset_name, repo_filter)
    return render_template(
        "index.html",
        dataset_name=dataset_name,
        dataset_title=store.DATASET_TITLES.get(dataset_name, dataset_name.title()),
        columns=dataset["columns"],
        records=table_rows,
        summary=store.summary_counts,
        dataset_titles=store.DATASET_TITLES,
        repo_filter=repo_filter,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str) -> str:
    if dataset_name not in store.datasets:
        abort(404)
    record = store.get_record(dataset_name, record_id)
    if not record:
        abort(404)
    related = store.get_related(dataset_name, record)
    details = store.strip_internal(record)
    return render_template(
        "dataset_detail.html",
        dataset_name=dataset_name,
        dataset_title=store.DATASET_TITLES.get(dataset_name, dataset_name.title()),
        dataset_titles=store.DATASET_TITLES,
        record=details,
        related=related,
    )


@app.route("/visualize")
def visualize() -> str:
    repo_filter = request.args.get("repo")
    repo_key = repo_filter or ""
    merged_repo_data = merged_repo_counts(repo_key)
    merged_time_data = merged_time_series(repo_key)
    pr_issue_data = closing_issue_distribution(repo_key)
    pr_histogram = pr_detail_month_histogram(repo_key)
    issue_labels = issue_label_usage(repo_key)
    return render_template(
        "visualize.html",
        dataset_titles=store.DATASET_TITLES,
        repo_filter=repo_filter,
        merged_repo_data=merged_repo_data,
        merged_time_data=merged_time_data,
        pr_issue_data=pr_issue_data,
        pr_histogram=pr_histogram,
        issue_labels=issue_labels,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    if dataset_name not in store.datasets:
        abort(404)
    repo_filter = request.args.get("repo")
    payload = store.get_api_payload(dataset_name, repo_filter)
    return jsonify({
        "dataset": dataset_name,
        "count": len(payload),
        "records": payload,
    })


@lru_cache(maxsize=64)
def merged_repo_counts(repo_filter: str = "") -> Dict[str, Any]:
    repo_filter = repo_filter or None
    records = store.get_records("merged_data", repo_filter)
    counts = Counter(record.get("repo", "Unknown") for record in records)
    top = counts.most_common(10)
    labels = [label for label, _ in top]
    values = [count for _, count in top]
    return {"labels": labels, "values": values}


@lru_cache(maxsize=128)
def merged_time_series(repo_filter: str = "") -> Dict[str, Any]:
    repo_filter = repo_filter or None
    records = store.get_records("merged_data", repo_filter)
    timeline: Dict[str, int] = defaultdict(int)
    for record in records:
        created = parse_iso_datetime(record.get("created_at"))
        if created:
            timeline[created.strftime("%Y-%m-%d")] += 1
    points = sorted(timeline.items())
    labels = [date for date, _ in points]
    values = [count for _, count in points]
    return {"labels": labels, "values": values}


@lru_cache(maxsize=64)
def closing_issue_distribution(repo_filter: str = "") -> Dict[str, Any]:
    repo_filter = repo_filter or None
    records = store.get_records("pr_issue", repo_filter)
    distribution: Dict[str, int] = defaultdict(int)
    for record in records:
        repo = record.get("repo", "Unknown")
        closing_issues = record.get("closing_issue") or []
        distribution[repo] += len(closing_issues)
    items = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
    labels = [label for label, _ in items]
    values = [value for _, value in items]
    return {"labels": labels, "values": values}


@lru_cache(maxsize=64)
def pr_detail_month_histogram(repo_filter: str = "") -> Dict[str, Any]:
    repo_filter = repo_filter or None
    records = store.get_records("pr_detail", repo_filter)
    histogram: Dict[str, int] = defaultdict(int)
    for record in records:
        created = parse_iso_datetime(record.get("created_at"))
        if created:
            histogram[created.strftime("%Y-%m")] += 1
    items = sorted(histogram.items())
    labels = [label for label, _ in items]
    values = [value for _, value in items]
    return {"labels": labels, "values": values}


@lru_cache(maxsize=64)
def issue_label_usage(repo_filter: str = "") -> Dict[str, Any]:
    repo_filter = repo_filter or None
    records = store.get_records("issue_detail", repo_filter)
    label_counts: Counter[str] = Counter()
    for record in records:
        labels = record.get("labels") or []
        if isinstance(labels, list):
            label_counts.update(str(label) for label in labels)
    top = label_counts.most_common(10)
    labels = [label for label, _ in top]
    values = [count for _, count in top]
    return {"labels": labels, "values": values}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
