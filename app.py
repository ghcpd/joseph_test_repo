from __future__ import annotations

import json
from typing import Any, Dict, List

from flask import Flask, abort, jsonify, render_template, request

from data.manager import DataManager

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

data_manager = DataManager()


@app.template_filter("format_value")
def format_value(value: Any) -> str:
    if value in (None, ""):
        return "N/A"
    if isinstance(value, list):
        if all(isinstance(item, dict) and "name" in item for item in value):
            return ", ".join(item.get("name", "N/A") for item in value)
        return ", ".join(format_value(item) for item in value)
    if isinstance(value, dict):
        if "login" in value:
            return value.get("login") or "N/A"
        return json.dumps(value, ensure_ascii=False)
    return str(value)


@app.route("/")
def index() -> str:
    default_dataset = request.args.get("dataset", "merged_data")
    dataset_tables = data_manager.get_all_data_for_template()
    if default_dataset not in dataset_tables:
        default_dataset = "merged_data"
    summary = data_manager.get_summary()
    dataset_metadata = data_manager.get_dataset_metadata()
    return render_template(
        "index.html",
        summary=summary,
        dataset_tables=dataset_tables,
        default_dataset=default_dataset,
        dataset_metadata=dataset_metadata,
    )


@app.route("/dataset/<dataset_name>/<path:record_id>")
def dataset_detail(dataset_name: str, record_id: str) -> str:
    record = data_manager.get_record(dataset_name, record_id)
    if not record:
        abort(404)
    related = data_manager.get_related_records(dataset_name, record)
    dataset_config = data_manager.DATASETS.get(dataset_name, {})
    return render_template(
        "detail.html",
        dataset_name=dataset_name,
        dataset_display=dataset_config.get("display", dataset_name),
        record=record,
        related=related,
        dataset_configs=data_manager.DATASETS,
    )


@app.route("/visualize")
def visualize() -> str:
    repo_filter = request.args.get("repo")
    aggregations = data_manager.get_aggregations(repo_filter)
    repos = data_manager.get_all_repos()
    return render_template(
        "visualize.html",
        aggregations=aggregations,
        repo_filter=repo_filter,
        repos=repos,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    if dataset_name not in data_manager.DATASETS:
        abort(404)
    repo_filter = request.args.get("repo")
    records = data_manager.get_dataset(dataset_name, repo_filter)
    return jsonify({"data": records})


@app.errorhandler(404)
def not_found(error):  # type: ignore[override]
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
