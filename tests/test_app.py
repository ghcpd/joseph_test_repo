import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import app, data_store


def get_client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_home_page():
    client = get_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"PR Search Results" in response.data


def test_dataset_detail():
    client = get_client()
    dataset = data_store["merged_data"]
    record_id = next(iter(dataset["index"].keys()))
    response = client.get(f"/dataset/merged_data/{record_id}")
    assert response.status_code == 200
    assert b"Merged PR/Issue Data" in response.data


def test_dataset_api_filter():
    client = get_client()
    response = client.get("/api/pr_detail?repo=octocat/hello-world")
    assert response.status_code == 200
    data = response.get_json()
    assert all(record["repo"] == "octocat/hello-world" for record in data)


def test_visualize_page():
    client = get_client()
    response = client.get("/visualize")
    assert response.status_code == 200
    assert b"Top Repositories by PR Count" in response.data


def test_detail_not_found():
    client = get_client()
    response = client.get("/dataset/pr_detail/9999")
    assert response.status_code == 404