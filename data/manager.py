from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _extract_repo_full_name_from_url(url: Optional[str]) -> str:
    if not url:
        return "Unknown"
    parts = url.strip("/").split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return url


class DataManager:
    DATASETS = {
        "merged_data": {
            "file": "output_data/merged_data.jsonl",
            "display": "Merged PR/Issue Data",
            "table_fields": ["repo", "issue_number", "issue_title", "pull_number", "created_at"],
        },
        "pr_issue": {
            "file": "input_data/pr_issue_single.jsonl",
            "display": "PR Issue Search Results",
            "table_fields": ["repo_full_name", "number", "title", "state", "closing_issue", "created_at"],
        },
        "pr_detail": {
            "file": "input_data/pr_detail.jsonl",
            "display": "Pull Request Details",
            "table_fields": ["repo_full_name", "number", "title", "state", "created_at", "user_login"],
        },
        "issue_detail": {
            "file": "input_data/issue_detail.jsonl",
            "display": "Issue Details",
            "table_fields": ["repo_full_name", "number", "title", "state", "created_at", "user_login"],
        },
    }

    def __init__(self) -> None:
        self.datasets: Dict[str, List[Dict]] = {}
        self.indexes: Dict[str, Dict[str, Dict]] = {}
        self.fields: Dict[str, List[str]] = {}
        self.all_repos: List[str] = []
        self.pr_lookup: Dict[tuple, Dict] = {}
        self.issue_lookup: Dict[tuple, Dict] = {}
        self.pr_issue_lookup: Dict[tuple, Dict] = {}
        self.aggregation_cache: Dict[str, Dict] = {}
        self.load()

    def load(self) -> None:
        repos = set()
        for dataset_name, config in self.DATASETS.items():
            path = BASE_DIR / config["file"]
            records: List[Dict] = []
            index: Dict[str, Dict] = {}
            fields = set()
            if not path.exists():
                self.datasets[dataset_name] = []
                self.indexes[dataset_name] = {}
                self.fields[dataset_name] = []
                continue
            with path.open("r", encoding="utf-8") as fh:
                for raw_line in fh:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    record = json.loads(raw_line)
                    enriched = self._enrich_record(dataset_name, record)
                    record_id = self._build_identifier(dataset_name, enriched)
                    enriched["__id"] = record_id
                    records.append(enriched)
                    index[record_id] = enriched
                    fields.update(enriched.keys())
                    repo_name = enriched.get("repo_full_name") or enriched.get("repo")
                    if isinstance(repo_name, str):
                        repos.add(repo_name)
            field_list = sorted(field for field in fields if field != "__id")
            self.datasets[dataset_name] = records
            self.indexes[dataset_name] = index
            self.fields[dataset_name] = field_list
        self.all_repos = sorted(repo for repo in repos if repo)
        self.aggregation_cache.clear()

    def _enrich_record(self, dataset_name: str, record: Dict) -> Dict:
        enriched = dict(record)
        if dataset_name == "pr_issue":
            repo_name = _extract_repo_full_name_from_url(record.get("repository_url"))
            enriched["repo_full_name"] = repo_name
            key = (repo_name, record.get("number"))
            self.pr_issue_lookup[key] = enriched
        elif dataset_name == "pr_detail":
            repo_name = (
                record.get("base", {})
                .get("repo", {})
                .get("full_name")
                or record.get("head", {})
                .get("repo", {})
                .get("full_name")
                or "Unknown"
            )
            enriched["repo_full_name"] = repo_name
            enriched["user_login"] = record.get("user", {}).get("login")
            key = (repo_name, record.get("number"))
            self.pr_lookup[key] = enriched
        elif dataset_name == "issue_detail":
            repo_name = (
                record.get("repository", {})
                .get("full_name")
                or record.get("repo", {})
                .get("full_name")
                or "Unknown"
            )
            enriched["repo_full_name"] = repo_name
            enriched["user_login"] = record.get("user", {}).get("login")
            key = (repo_name, record.get("number"))
            self.issue_lookup[key] = enriched
        elif dataset_name == "merged_data":
            repo_name = record.get("repo") or "Unknown"
            if repo_name:
                key = (repo_name, record.get("pull_number"))
                self.pr_lookup.setdefault(key, None)
        return enriched

    def _build_identifier(self, dataset_name: str, record: Dict) -> str:
        repo = record.get("repo_full_name") or record.get("repo") or "Unknown"
        if dataset_name in {"pr_issue", "pr_detail", "issue_detail"}:
            number = record.get("number")
        else:
            number = record.get("pull_number") or record.get("issue_number")
        return f"{dataset_name}:{repo}:{number}"

    def get_dataset(self, dataset_name: str, repo_filter: Optional[str] = None) -> List[Dict]:
        records = self.datasets.get(dataset_name, [])
        if repo_filter:
            return [record for record in records if self._matches_repo(record, repo_filter)]
        return records

    def get_dataset_metadata(self) -> List[Dict]:
        results = []
        for name, config in self.DATASETS.items():
            results.append(
                {
                    "name": name,
                    "display": config["display"],
                    "fields": self.get_table_fields(name),
                }
            )
        return results

    def get_table_fields(self, dataset_name: str) -> List[str]:
        config = self.DATASETS.get(dataset_name, {})
        if "table_fields" in config:
            return config["table_fields"]
        return self.fields.get(dataset_name, [])

    def get_summary(self) -> Dict[str, int]:
        return {
            self.DATASETS[name]["display"]: len(records)
            for name, records in self.datasets.items()
        }

    def get_record(self, dataset_name: str, record_id: str) -> Optional[Dict]:
        return self.indexes.get(dataset_name, {}).get(record_id)

    def _matches_repo(self, record: Dict, repo_filter: str) -> bool:
        repo_name = record.get("repo_full_name") or record.get("repo")
        return repo_filter.lower() == repo_name.lower()

    def get_all_data_for_template(self) -> Dict[str, Dict]:
        tables = {}
        for name, config in self.DATASETS.items():
            tables[name] = {
                "display": config["display"],
                "fields": self.get_table_fields(name),
                "records": self.datasets.get(name, []),
            }
        return tables

    def get_related_records(self, dataset_name: str, record: Dict) -> List[Dict]:
        repo = record.get("repo_full_name") or record.get("repo")
        number = record.get("number")
        related: List[Dict] = []
        if dataset_name == "pr_detail":
            key = (repo, number)
            pr_issue_record = self.pr_issue_lookup.get(key)
            if pr_issue_record:
                related.append(
                    {
                        "label": "Linked Issue",
                        "dataset": "issue_detail",
                        "records": self._find_issues_from_pr_issue(pr_issue_record),
                    }
                )
            related.append(
                {
                    "label": "PR Issue Search Entry",
                    "dataset": "pr_issue",
                    "records": [pr_issue_record] if pr_issue_record else [],
                }
            )
        elif dataset_name == "issue_detail":
            matches = self._find_prs_for_issue(repo, record.get("number"))
            related.append(
                {
                    "label": "Related Pull Requests",
                    "dataset": "pr_detail",
                    "records": matches,
                }
            )
        elif dataset_name == "pr_issue":
            if repo:
                issue_number = record.get("closing_issue")
                pr_number = record.get("number")
                pr_record = self.pr_lookup.get((repo, pr_number))
                issue_record = self.issue_lookup.get((repo, issue_number))
                if pr_record:
                    related.append(
                        {
                            "label": "Pull Request Detail",
                            "dataset": "pr_detail",
                            "records": [pr_record],
                        }
                    )
                if issue_record:
                    related.append(
                        {
                            "label": "Issue Detail",
                            "dataset": "issue_detail",
                            "records": [issue_record],
                        }
                    )
        elif dataset_name == "merged_data":
            pr_record = self.pr_lookup.get((record.get("repo"), record.get("pull_number")))
            issue_number = record.get("issue_number")
            issue_record = (
                self.issue_lookup.get((record.get("repo"), issue_number))
                if issue_number is not None
                else None
            )
            pr_issue_record = (
                self.pr_issue_lookup.get((record.get("repo"), record.get("pull_number")))
            )
            related.append(
                {
                    "label": "Pull Request Detail",
                    "dataset": "pr_detail",
                    "records": [pr_record] if pr_record else [],
                }
            )
            related.append(
                {
                    "label": "Issue Detail",
                    "dataset": "issue_detail",
                    "records": [issue_record] if issue_record else [],
                }
            )
            related.append(
                {
                    "label": "PR Issue Search Entry",
                    "dataset": "pr_issue",
                    "records": [pr_issue_record] if pr_issue_record else [],
                }
            )
        return related

    def _find_issues_from_pr_issue(self, pr_issue_record: Optional[Dict]) -> List[Dict]:
        if not pr_issue_record:
            return []
        repo = pr_issue_record.get("repo_full_name")
        issue_number = pr_issue_record.get("closing_issue")
        issue = self.issue_lookup.get((repo, issue_number))
        return [issue] if issue else []

    def _find_prs_for_issue(self, repo: Optional[str], issue_number: Optional[int]) -> List[Dict]:
        if not repo or issue_number is None:
            return []
        results = []
        for (pr_repo, pr_number), record in self.pr_issue_lookup.items():
            if pr_repo == repo and record.get("closing_issue") == issue_number:
                pr = self.pr_lookup.get((repo, pr_number))
                if pr:
                    results.append(pr)
        return results

    def get_aggregations(self, repo_filter: Optional[str] = None) -> Dict:
        cache_key = repo_filter.lower() if repo_filter else "__all__"
        if cache_key in self.aggregation_cache:
            return self.aggregation_cache[cache_key]
        aggregates = {
            "merged_repo_counts": self._merged_repo_counts(repo_filter),
            "merged_time_series": self._merged_time_series(repo_filter),
            "pr_issue_closing_distribution": self._pr_issue_closing_distribution(repo_filter),
            "pr_detail_monthly_histogram": self._pr_detail_monthly_histogram(repo_filter),
            "issue_detail_top_labels": self._issue_detail_top_labels(repo_filter),
        }
        self.aggregation_cache[cache_key] = aggregates
        return aggregates

    def _merged_repo_counts(self, repo_filter: Optional[str]) -> Dict:
        records = self.get_dataset("merged_data", repo_filter)
        counter = Counter(record.get("repo") for record in records if record.get("repo"))
        most_common = counter.most_common(10)
        return {
            "repos": [item[0] for item in most_common],
            "counts": [item[1] for item in most_common],
        }

    def _merged_time_series(self, repo_filter: Optional[str]) -> Dict:
        records = self.get_dataset("merged_data", repo_filter)
        counter = Counter()
        for record in records:
            dt = _parse_iso_datetime(record.get("created_at"))
            if dt:
                date_key = dt.strftime("%Y-%m-%d")
                counter[date_key] += 1
        dates = sorted(counter.keys())
        return {
            "dates": dates,
            "counts": [counter[date] for date in dates],
        }

    def _pr_issue_closing_distribution(self, repo_filter: Optional[str]) -> Dict:
        records = self.get_dataset("pr_issue", repo_filter)
        repo_counter: Dict[str, int] = defaultdict(int)
        for record in records:
            repo = record.get("repo_full_name")
            closing_issue = record.get("closing_issue")
            if repo and closing_issue:
                repo_counter[repo] += 1
        repos = sorted(repo_counter.keys(), key=lambda r: repo_counter[r], reverse=True)
        return {
            "repos": repos,
            "counts": [repo_counter[repo] for repo in repos],
        }

    def _pr_detail_monthly_histogram(self, repo_filter: Optional[str]) -> Dict:
        records = self.get_dataset("pr_detail", repo_filter)
        counter = Counter()
        for record in records:
            dt = _parse_iso_datetime(record.get("created_at"))
            if dt:
                month_key = dt.strftime("%Y-%m")
                counter[month_key] += 1
        months = sorted(counter.keys())
        return {
            "months": months,
            "counts": [counter[month] for month in months],
        }

    def _issue_detail_top_labels(self, repo_filter: Optional[str]) -> Dict:
        records = self.get_dataset("issue_detail", repo_filter)
        label_counter = Counter()
        for record in records:
            labels = record.get("labels", [])
            for label in labels:
                name = label.get("name") if isinstance(label, dict) else label
                if name:
                    label_counter[name] += 1
        most_common = label_counter.most_common(10)
        return {
            "labels": [item[0] for item in most_common],
            "counts": [item[1] for item in most_common],
        }

    def get_all_repos(self) -> List[str]:
        return self.all_repos
