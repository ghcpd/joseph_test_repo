import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATHS = {
    "pr_issue": BASE_DIR / "input_data" / "pr_issue_single.jsonl",
    "pr_detail": BASE_DIR / "input_data" / "pr_detail.jsonl",
    "issue_detail": BASE_DIR / "input_data" / "issue_detail.jsonl",
    "merged_data": BASE_DIR / "output_data" / "merged_data.jsonl",
}

PREFERRED_KEYS = {
    "pr_issue": ["id", "number"],
    "pr_detail": ["id", "number"],
    "issue_detail": ["id", "number"],
    "merged_data": ["id", "issue_number", "pull_number"],
}

MERGED_DISPLAY_FIELDS = ["repo", "issue_number", "issue_title", "pull_number", "created_at"]


class DataStore:
    """Central location for loading and querying dataset information."""

    def __init__(self) -> None:
        self.datasets: Dict[str, List[Dict[str, Any]]] = {}
        self.indexes: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._aggregation_cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_datasets()

    def _load_all_datasets(self) -> None:
        for dataset_name, path in DATASET_PATHS.items():
            records = self._load_dataset(dataset_name, path)
            self.datasets[dataset_name] = records
            self.indexes[dataset_name] = {
                record["_record_id"]: record for record in records
            }

    def _load_dataset(self, dataset_name: str, path: Path) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not path.exists():
            return records

        with path.open("r", encoding="utf-8") as handle:
            for idx, line in enumerate(handle):
                raw_line = line.strip()
                if not raw_line:
                    continue
                try:
                    raw_record = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                normalized = self._normalize_record(dataset_name, raw_record, idx)
                records.append(normalized)
        return records

    def _normalize_record(
        self, dataset_name: str, record: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        normalized = dict(record)
        normalized["_record_id"] = self._generate_record_id(
            dataset_name, normalized, index
        )
        repo_value = self._extract_repo(dataset_name, normalized)
        if repo_value:
            normalized.setdefault("repo", repo_value)
        return normalized

    def _generate_record_id(
        self, dataset_name: str, record: Dict[str, Any], index: int
    ) -> str:
        for key in PREFERRED_KEYS.get(dataset_name, []):
            value = record.get(key)
            if value in (None, "", []):
                continue
            if isinstance(value, (list, dict)):
                continue
            return str(value)
        if dataset_name == "merged_data":
            repo = record.get("repo", "unknown")
            issue_number = record.get("issue_number", index)
            return f"{repo}:{issue_number}"
        return str(index)

    @staticmethod
    def _extract_repo(dataset_name: str, record: Dict[str, Any]) -> Optional[str]:
        if dataset_name == "pr_detail":
            return (
                record.get("base", {})
                .get("repo", {})
                .get("full_name")
            )
        if dataset_name in {"pr_issue", "issue_detail"}:
            url = record.get("repository_url")
            return DataStore._repo_from_url(url)
        if dataset_name == "merged_data":
            return record.get("repo")
        return None

    @staticmethod
    def _repo_from_url(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        marker = "/repos/"
        if marker in url:
            return url.split(marker, 1)[-1]
        return url.rsplit("/", 1)[-1] if "/" in url else url

    def get_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        return self.datasets.get(dataset_name, [])

    def get_record(self, dataset_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        return self.indexes.get(dataset_name, {}).get(record_id)

    def find_by_field(
        self, dataset_name: str, field: str, value: Any
    ) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        for record in self.get_dataset(dataset_name):
            if str(record.get(field)) == str(value):
                return record
        return None

    @property
    def dataset_names(self) -> List[str]:
        return list(DATASET_PATHS.keys())

    def summary_counts(self) -> Dict[str, int]:
        return {name: len(records) for name, records in self.datasets.items()}

    def display_fields(self, dataset_name: str) -> List[str]:
        if dataset_name == "merged_data":
            return MERGED_DISPLAY_FIELDS
        dataset = self.get_dataset(dataset_name)
        if not dataset:
            return []
        keys: List[str] = []
        for record in dataset:
            for key in record.keys():
                if key.startswith("_"):
                    continue
                if key not in keys:
                    keys.append(key)
        return keys

    def related_entries(
        self, dataset_name: str, record: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        related: List[Dict[str, Any]] = []
        if dataset_name == "pr_detail":
            issue = self._issue_for_pr(record)
            if issue:
                related.append(
                    {
                        "label": "Linked Issue",
                        "dataset": "issue_detail",
                        "record": issue,
                    }
                )
            merged = self._merged_for_pr(record)
            for entry in merged:
                related.append(
                    {
                        "label": "Merged Data Entry",
                        "dataset": "merged_data",
                        "record": entry,
                    }
                )
            pr_issue = self.find_by_field(
                "pr_issue", "number", record.get("number")
            )
            if pr_issue:
                related.append(
                    {
                        "label": "PR Search Entry",
                        "dataset": "pr_issue",
                        "record": pr_issue,
                    }
                )
        elif dataset_name == "issue_detail":
            pr = self._pr_for_issue(record)
            if pr:
                related.append(
                    {
                        "label": "Linked Pull Request",
                        "dataset": "pr_detail",
                        "record": pr,
                    }
                )
            merged = self._merged_for_issue(record)
            for entry in merged:
                related.append(
                    {
                        "label": "Merged Data Entry",
                        "dataset": "merged_data",
                        "record": entry,
                    }
                )
        elif dataset_name == "merged_data":
            pr = self.find_by_field(
                "pr_detail", "number", record.get("pull_number")
            )
            if pr:
                related.append(
                    {
                        "label": "Pull Request Detail",
                        "dataset": "pr_detail",
                        "record": pr,
                    }
                )
            issue = self.find_by_field(
                "issue_detail", "number", record.get("issue_number")
            )
            if issue:
                related.append(
                    {
                        "label": "Issue Detail",
                        "dataset": "issue_detail",
                        "record": issue,
                    }
                )
            search = self.find_by_field(
                "pr_issue", "number", record.get("pull_number")
            )
            if search:
                related.append(
                    {
                        "label": "PR Search Entry",
                        "dataset": "pr_issue",
                        "record": search,
                    }
                )
        elif dataset_name == "pr_issue":
            pr = self.find_by_field(
                "pr_detail", "number", record.get("number")
            )
            if pr:
                related.append(
                    {
                        "label": "Pull Request Detail",
                        "dataset": "pr_detail",
                        "record": pr,
                    }
                )
            issue = self.find_by_field(
                "issue_detail", "number", record.get("closing_issue")
            )
            if issue:
                related.append(
                    {
                        "label": "Issue Detail",
                        "dataset": "issue_detail",
                        "record": issue,
                    }
                )
        return related

    def _issue_for_pr(self, pr_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        issue_url = pr_record.get("issue_url")
        issue_number = self._extract_number_from_url(issue_url)
        if issue_number is None:
            return None
        return self.find_by_field("issue_detail", "number", issue_number)

    def _pr_for_issue(self, issue_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pull_request = issue_record.get("pull_request", {})
        pr_url = pull_request.get("url") if isinstance(pull_request, dict) else None
        pr_number = self._extract_number_from_url(pr_url)
        if pr_number is None:
            return None
        return self.find_by_field("pr_detail", "number", pr_number)

    def _merged_for_pr(self, pr_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        number = pr_record.get("number")
        if number is None:
            return []
        return [
            entry
            for entry in self.get_dataset("merged_data")
            if str(entry.get("pull_number")) == str(number)
        ]

    def _merged_for_issue(self, issue_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        number = issue_record.get("number")
        if number is None:
            return []
        return [
            entry
            for entry in self.get_dataset("merged_data")
            if str(entry.get("issue_number")) == str(number)
        ]

    @staticmethod
    def _extract_number_from_url(url: Optional[str]) -> Optional[int]:
        if not url:
            return None
        parts = [part for part in url.split("/") if part]
        if not parts:
            return None
        tail = parts[-1]
        try:
            return int(tail)
        except ValueError:
            return None

    def filtered_dataset(self, dataset_name: str, repo: Optional[str]) -> List[Dict[str, Any]]:
        if not repo:
            return list(self.get_dataset(dataset_name))
        repo_lower = repo.lower()
        return [
            record
            for record in self.get_dataset(dataset_name)
            if str(record.get("repo", "")).lower() == repo_lower
        ]

    def visualization_data(self, repo: Optional[str] = None) -> Dict[str, Any]:
        cache_key = repo.lower() if repo else "__all__"
        if cache_key in self._aggregation_cache:
            return self._aggregation_cache[cache_key]

        data = {
            "merged_top_repos": self._merged_top_repos(repo),
            "merged_time_series": self._merged_time_series(repo),
            "pr_issue_closing_distribution": self._closing_distribution(repo),
            "pr_detail_month_distribution": self._pr_detail_months(repo),
            "issue_detail_top_labels": self._issue_top_labels(repo),
        }
        self._aggregation_cache[cache_key] = data
        return data

    def _merged_top_repos(self, repo: Optional[str]) -> Dict[str, Any]:
        records = self.filtered_dataset("merged_data", repo)
        counter = Counter()
        for record in records:
            repo_name = record.get("repo")
            if not repo_name:
                continue
            if record.get("pull_number") is None:
                continue
            counter[repo_name] += 1
        most_common = counter.most_common(10)
        labels = [item[0] for item in most_common]
        values = [item[1] for item in most_common]
        return {"labels": labels, "values": values}

    def _merged_time_series(self, repo: Optional[str]) -> Dict[str, Any]:
        records = self.filtered_dataset("merged_data", repo)
        counter: Dict[str, int] = defaultdict(int)
        for record in records:
            created_at = record.get("created_at")
            month_key = self._month_key(created_at)
            if not month_key:
                continue
            counter[month_key] += 1
        sorted_items = sorted(counter.items())
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        return {"labels": labels, "values": values}

    def _closing_distribution(self, repo: Optional[str]) -> Dict[str, Any]:
        records = self.filtered_dataset("pr_issue", repo)
        counter: Dict[str, int] = defaultdict(int)
        for record in records:
            repo_name = record.get("repo")
            if not repo_name:
                continue
            closing_issue = record.get("closing_issue")
            count = self._closing_issue_count(closing_issue)
            counter[repo_name] += count
        sorted_items = sorted(counter.items(), key=lambda item: item[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        return {"labels": labels[:10], "values": values[:10]}

    def _pr_detail_months(self, repo: Optional[str]) -> Dict[str, Any]:
        records = self.filtered_dataset("pr_detail", repo)
        counter: Dict[str, int] = defaultdict(int)
        for record in records:
            created_at = record.get("created_at")
            month_key = self._month_key(created_at)
            if not month_key:
                continue
            counter[month_key] += 1
        sorted_items = sorted(counter.items())
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        return {"labels": labels, "values": values}

    def _issue_top_labels(self, repo: Optional[str]) -> Dict[str, Any]:
        records = self.filtered_dataset("issue_detail", repo)
        counter: Counter[str] = Counter()
        for record in records:
            labels = record.get("labels")
            if isinstance(labels, list):
                for item in labels:
                    if isinstance(item, dict):
                        name = item.get("name")
                    else:
                        name = str(item)
                    if name:
                        counter[name] += 1
        most_common = counter.most_common(10)
        labels = [item[0] for item in most_common]
        values = [item[1] for item in most_common]
        return {"labels": labels, "values": values}

    @staticmethod
    def _closing_issue_count(value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            return len(value)
        try:
            return int(bool(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _month_key(timestamp: Optional[str]) -> Optional[str]:
        if not timestamp:
            return None
        ts = timestamp
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            return None
        return dt.strftime("%Y-%m")


def serialize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a record for JSON serialization."""
    serialized: Dict[str, Any] = {}
    for key, value in record.items():
        if key.startswith("_"):
            serialized[key] = value
        elif isinstance(value, (str, int, float, type(None), bool)):
            serialized[key] = value
        else:
            try:
                json.dumps(value)
            except TypeError:
                serialized[key] = str(value)
            else:
                serialized[key] = value
    return serialized
