from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import app, compute_visualization_data, datasets


def test_datasets_loaded():
    expected_keys = {"pr_issue", "pr_detail", "issue_detail", "merged_data"}
    assert expected_keys.issubset(datasets.keys())
    for key in expected_keys:
        assert len(datasets[key]["records"]) > 0
        assert isinstance(datasets[key]["display_fields"], list)


def test_visualization_data_structure():
    data = compute_visualization_data(None)
    expected_sections = {
        "top_repos",
        "time_series",
        "closing_issue_distribution",
        "pr_month_histogram",
        "top_labels",
    }
    assert expected_sections.issubset(data.keys())
    for section in expected_sections:
        assert "labels" in data[section]
        assert "values" in data[section]


def test_api_endpoint_returns_json():
    client = app.test_client()
    response = client.get("/api/pr_detail")
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)
    assert all(isinstance(item, dict) for item in payload)