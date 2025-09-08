from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, render_template, request, url_for

app = Flask(__name__)

# Data containers
DATA_DIR = Path(__file__).resolve().parent
PR_ISSUE_FILE = DATA_DIR / "input_data" / "pr_issue_single.jsonl"
PR_DETAIL_FILE = DATA_DIR / "input_data" / "pr_detail.jsonl"
ISSUE_DETAIL_FILE = DATA_DIR / "input_data" / "issue_detail.jsonl"
MERGED_DATA_FILE = DATA_DIR / "output_data" / "merged_data.jsonl"

# In-memory datasets
pr_issue_records: List[Dict[str, Any]] = []
pr_detail_records: List[Dict[str, Any]] = []
issue_detail_records: List[Dict[str, Any]] = []
merged_data_records: List[Dict[str, Any]] = []

# Indexes for quick lookup
pr_issue_by_id: Dict[str, Dict[str, Any]] = {}
pr_issue_by_pr_url: Dict[str, List[Dict[str, Any]]] = {}

pr_detail_by_id: Dict[str, Dict[str, Any]] = {}
pr_detail_by_url: Dict[str, Dict[str, Any]] = {}

issue_detail_by_id: Dict[str, Dict[str, Any]] = {}
issue_detail_by_number: Dict[int, Dict[str, Any]] = {}

merged_data_by_id: Dict[str, Dict[str, Any]] = {}

# Simple cache for aggregations
agg_cache: Dict[Tuple[str, Optional[str]], Any] = {}

def _safe_str(v: Any) -> str:
    return "N/A" if v is None else str(v)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    if not path.exists():
        return recs
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                continue
    return recs


def build_indexes() -> None:
    # pr_issue
    for obj in pr_issue_records:
        rid = str(obj.get("id") or obj.get("node_id") or obj.get("number") or len(pr_issue_by_id))
        pr_issue_by_id[rid] = obj
        pr_obj = obj.get("pull_request")
        if isinstance(pr_obj, dict):
            url = pr_obj.get("url")
            if url:
                pr_issue_by_pr_url.setdefault(url, []).append(obj)

    # pr_detail
    for obj in pr_detail_records:
        rid = str(obj.get("id") or obj.get("number") or len(pr_detail_by_id))
        pr_detail_by_id[rid] = obj
        url = obj.get("url")
        if url:
            pr_detail_by_url[url] = obj

    # issue_detail
    for obj in issue_detail_records:
        rid = str(obj.get("id") or obj.get("number") or len(issue_detail_by_id))
        issue_detail_by_id[rid] = obj
        num = obj.get("number")
        if num is not None:
            try:
                issue_detail_by_number[int(num)] = obj
            except Exception:
                pass

    # merged_data
    for idx, obj in enumerate(merged_data_records):
        rid = obj.get("instance_id") or f"merged-{idx}"
        merged_data_by_id[str(rid)] = obj


def load_all_data() -> None:
    global pr_issue_records, pr_detail_records, issue_detail_records, merged_data_records

    pr_issue_records = load_jsonl(PR_ISSUE_FILE)
    pr_detail_records = load_jsonl(PR_DETAIL_FILE)
    issue_detail_records = load_jsonl(ISSUE_DETAIL_FILE)
    merged_data_records = load_jsonl(MERGED_DATA_FILE)

    build_indexes()


# Load data at import time for Flask >=3.1
load_all_data()


def dataset_metadata() -> List[Dict[str, Any]]:
    return [
        {"name": "pr_issue", "display": "PR Issue Search Results", "count": len(pr_issue_records)},
        {"name": "pr_detail", "display": "PR Details", "count": len(pr_detail_records)},
        {"name": "issue_detail", "display": "Issue Details", "count": len(issue_detail_records)},
        {"name": "merged_data", "display": "Merged Data", "count": len(merged_data_records)},
    ]


def get_dataset(name: str) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    if name == "pr_issue":
        return pr_issue_records, pr_issue_by_id
    if name == "pr_detail":
        return pr_detail_records, pr_detail_by_id
    if name == "issue_detail":
        return issue_detail_records, issue_detail_by_id
    if name == "merged_data":
        return merged_data_records, merged_data_by_id
    return [], {}


@app.route("/")
def index():
    dataset = request.args.get("dataset", "merged_data")
    records, id_map = get_dataset(dataset)

    # Determine columns dynamically
    columns: List[str]
    if dataset == "merged_data":
        columns = ["repo", "issue_number", "issue_title", "pull_number", "created_at"]
    else:
        # union of keys of first few records
        keys = set()
        for obj in records[:50]:
            if isinstance(obj, dict):
                keys.update(obj.keys())
        columns = sorted(keys)[:10]  # limit columns for readability

    # Prepare rows with id (limit to keep UI responsive)
    limit = 200
    try:
        limit = int(request.args.get("limit", limit))
    except Exception:
        pass
    display_rows = []
    for i, (rid, obj) in enumerate(id_map.items()):
        if i >= limit:
            break
        row = {"_id": rid}
        for k in columns:
            row[k] = obj.get(k)
        display_rows.append(row)

    return render_template(
        "index.html",
        datasets=dataset_metadata(),
        active_dataset=dataset,
        columns=columns,
        rows=display_rows,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str):
    _, id_map = get_dataset(dataset_name)
    record = id_map.get(record_id)
    if not record:
        return render_template("detail.html", dataset=dataset_name, record_id=record_id, record=None, related={})

    related: Dict[str, Any] = {}
    # Related links logic
    if dataset_name == "pr_detail":
        pr_url = record.get("url")
        pr_issue_entries = pr_issue_by_pr_url.get(pr_url, [])
        if pr_issue_entries:
            closing_issue = pr_issue_entries[0].get("closing_issue")
            try:
                issue_num = int(closing_issue) if closing_issue is not None else None
            except Exception:
                issue_num = None
            issue_obj = issue_detail_by_number.get(issue_num) if issue_num is not None else None
            if issue_obj:
                # find the id key for this issue
                for iid, obj in issue_detail_by_id.items():
                    if obj is issue_obj:
                        related["issue_detail"] = {"id": iid, "title": obj.get("title")}
                        break
    elif dataset_name == "issue_detail":
        num = record.get("number")
        pr_issue_entries = []
        try:
            pr_issue_entries = [x for x in pr_issue_records if x.get("closing_issue") == num]
        except Exception:
            pass
        if pr_issue_entries:
            pr_url = None
            pr_obj = pr_issue_entries[0].get("pull_request")
            if isinstance(pr_obj, dict):
                pr_url = pr_obj.get("url")
            pr = pr_detail_by_url.get(pr_url) if pr_url else None
            if pr:
                for pid, obj in pr_detail_by_id.items():
                    if obj is pr:
                        related["pr_detail"] = {"id": pid, "title": obj.get("title")}
                        break
    elif dataset_name == "merged_data":
        repo = record.get("repo")
        issue_num = record.get("issue_number")
        pr_url = record.get("pr_url")
        issue_url = record.get("issue_url")
        pr = pr_detail_by_url.get(pr_url) if pr_url else None
        issue_obj = None
        try:
            issue_obj = issue_detail_by_number.get(int(issue_num)) if issue_num is not None else None
        except Exception:
            issue_obj = None
        if pr:
            for pid, obj in pr_detail_by_id.items():
                if obj is pr:
                    related["pr_detail"] = {"id": pid, "title": obj.get("title")}
                    break
        if issue_obj:
            for iid, obj in issue_detail_by_id.items():
                if obj is issue_obj:
                    related["issue_detail"] = {"id": iid, "title": obj.get("title")}
                    break
        # Also link back to pr_issue if possible
        if pr_url:
            pr_issue_entries = pr_issue_by_pr_url.get(pr_url, [])
            if pr_issue_entries:
                for sid, obj in pr_issue_by_id.items():
                    if obj is pr_issue_entries[0]:
                        related["pr_issue"] = {"id": sid, "title": obj.get("title") or obj.get("html_url")}
                        break

    return render_template("detail.html", dataset=dataset_name, record_id=record_id, record=record, related=related)


@app.route("/api/<dataset_name>")
def api_dataset(dataset_name: str):
    records, _ = get_dataset(dataset_name)
    repo_filter = request.args.get("repo")
    if repo_filter:
        filtered = []
        for obj in records:
            repo_val = obj.get("repo") or obj.get("full_name") or obj.get("base", {}).get("repo", {}).get("full_name")
            if repo_val == repo_filter:
                filtered.append(obj)
        return jsonify(filtered)
    return jsonify(records)


# Aggregations with simple cache

def get_merged_repo_counts(repo: Optional[str] = None):
    key = ("merged_repo_counts", repo)
    if key in agg_cache:
        return agg_cache[key]
    counts: Dict[str, int] = {}
    for obj in merged_data_records:
        r = obj.get("repo")
        if repo and r != repo:
            continue
        if r:
            counts[r] = counts.get(r, 0) + 1
    # top 10
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    agg_cache[key] = items
    return items


def get_merged_time_series(repo: Optional[str] = None):
    key = ("merged_time_series", repo)
    if key in agg_cache:
        return agg_cache[key]
    from collections import Counter
    from datetime import datetime

    counter: Counter = Counter()
    for obj in merged_data_records:
        if repo and obj.get("repo") != repo:
            continue
        ts = obj.get("created_at")
        if not ts:
            continue
        # Normalize to date (YYYY-MM-DD)
        try:
            date_str = ts[:10]
            datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue
        counter[date_str] += 1
    items = sorted(counter.items())
    agg_cache[key] = items
    return items


def get_pr_issue_closing_counts(repo: Optional[str] = None):
    key = ("pr_issue_closing_counts", repo)
    if key in agg_cache:
        return agg_cache[key]
    counts: Dict[str, int] = {}
    for obj in pr_issue_records:
        r = obj.get("full_name")
        if repo and r != repo:
            continue
        if obj.get("closing_issue") is not None and r:
            counts[r] = counts.get(r, 0) + 1
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    agg_cache[key] = items
    return items


def get_pr_detail_month_hist(repo: Optional[str] = None):
    key = ("pr_detail_month_hist", repo)
    if key in agg_cache:
        return agg_cache[key]
    from collections import Counter

    counter: Counter = Counter()
    for obj in pr_detail_records:
        # Repo name may be in base.repo.full_name
        if repo:
            base = obj.get("base") or {}
            base_repo = base.get("repo") or {}
            full_name = base_repo.get("full_name")
            if full_name != repo:
                continue
        ts = obj.get("created_at")
        if not ts:
            continue
        month = ts[:7]  # YYYY-MM
        counter[month] += 1
    items = sorted(counter.items())
    agg_cache[key] = items
    return items


def get_issue_label_top(repo: Optional[str] = None):
    key = ("issue_label_top", repo)
    if key in agg_cache:
        return agg_cache[key]
    from collections import Counter

    counter: Counter = Counter()
    for obj in issue_detail_records:
        if repo:
            repourl = obj.get("repository_url")
            # repository_url looks like https://api.github.com/repos/<owner>/<repo>
            if repourl and repourl.split("/repos/")[-1] != repo:
                continue
        labels = obj.get("labels")
        if isinstance(labels, list):
            for lab in labels:
                name = None
                if isinstance(lab, dict):
                    name = lab.get("name")
                elif isinstance(lab, str):
                    name = lab
                if name:
                    counter[name] += 1
    items = counter.most_common(10)
    agg_cache[key] = items
    return items


@app.route("/visualize")
def visualize():
    repo = request.args.get("repo")

    merged_counts = get_merged_repo_counts(repo)
    merged_time = get_merged_time_series(repo)
    pr_issue_counts = get_pr_issue_closing_counts(repo)
    pr_detail_hist = get_pr_detail_month_hist(repo)
    issue_label_top = get_issue_label_top(repo)

    return render_template(
        "visualize.html",
        repo=repo,
        merged_counts=merged_counts,
        merged_time=merged_time,
        pr_issue_counts=pr_issue_counts,
        pr_detail_hist=pr_detail_hist,
        issue_label_top=issue_label_top,
    )


def _run() -> None:
    import os
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    load_all_data()
    _run()
