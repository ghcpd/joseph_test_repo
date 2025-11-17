import json
from typing import Any, Dict, List

from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    url_for,
)

from data import DataStore, serialize_record

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

data_store = DataStore()

DATASET_LABELS = {
    "pr_issue": "PR Issue Search",
    "pr_detail": "Pull Request Detail",
    "issue_detail": "Issue Detail",
    "merged_data": "Merged Data",
}


@app.template_filter("format_value")
def format_value(value: Any) -> str:
    if value is None or value == "" or value == []:
        return "N/A"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, indent=2, sort_keys=True)
        except TypeError:
            return str(value)
    return str(value)


@app.context_processor
def inject_dataset_labels() -> Dict[str, str]:
    return {"dataset_labels": DATASET_LABELS}


@app.route("/")
def index() -> str:
    selected_dataset = request.args.get("dataset", "merged_data")
    if selected_dataset not in data_store.dataset_names:
        selected_dataset = "merged_data"

    summary = data_store.summary_counts()
    records = data_store.get_dataset(selected_dataset)
    fields = data_store.display_fields(selected_dataset)

    return render_template(
        "index.html",
        selected_dataset=selected_dataset,
        summary=summary,
        records=records,
        fields=fields,
        dataset_names=data_store.dataset_names,
    )


@app.route("/dataset/<dataset_name>/<record_id>")
def dataset_detail(dataset_name: str, record_id: str) -> str:
    if dataset_name not in data_store.dataset_names:
        abort(404)
    record = data_store.get_record(dataset_name, record_id)
    if not record:
        abort(404)
    related = data_store.related_entries(dataset_name, record)
    return render_template(
        "dataset_detail.html",
        dataset_name=dataset_name,
        record=record,
        related=related,
    )


@app.route("/visualize")
def visualize() -> str:
    repo = request.args.get("repo")
    repo = repo.strip() if repo else None
    visualization = data_store.visualization_data(repo)
    return render_template(
        "visualize.html",
        repo_filter=repo,
        visualization=visualization,
    )


@app.route("/api/<dataset_name>")
def dataset_api(dataset_name: str):
    if dataset_name not in data_store.dataset_names:
        abort(404)
    repo = request.args.get("repo")
    repo = repo.strip() if repo else None
    records = data_store.filtered_dataset(dataset_name, repo)
    serialized = [serialize_record(record) for record in records]
    return jsonify(serialized)


def dataset_display_name(dataset_name: str) -> str:
    return DATASET_LABELS.get(dataset_name, dataset_name.replace("_", " ").title())


@app.template_filter("dataset_display_name")
def dataset_display_name_filter(dataset_name: str) -> str:
    return dataset_display_name(dataset_name)


@app.template_global()
def record_detail_url(dataset_name: str, record: Dict[str, Any]) -> str:
    return url_for(
        "dataset_detail",
        dataset_name=dataset_name,
        record_id=record.get("_record_id"),
    )


if __name__ == "__main__":
    app.run(debug=True)
