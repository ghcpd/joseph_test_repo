from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import app, data_manager


@pytest.fixture
def client():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_data_manager_loads_datasets():
    counts = {name: len(data_manager.get_dataset(name)) for name in data_manager.DATASETS.keys()}
    assert counts["merged_data"] >= 1
    assert counts["pr_issue"] >= 1
    assert counts["pr_detail"] >= 1
    assert counts["issue_detail"] >= 1


def test_index_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"GitHub Pull Request" in response.data


def test_dataset_detail_page(client):
    dataset = data_manager.get_dataset("merged_data")[0]
    response = client.get(f"/dataset/merged_data/{dataset['__id']}")
    assert response.status_code == 200
    assert dataset["repo"].encode() in response.data


def test_api_endpoint_returns_json(client):
    response = client.get("/api/pr_detail")
    assert response.status_code == 200
    payload = response.get_json()
    assert "data" in payload
    assert isinstance(payload["data"], list)


def test_visualization_page(client):
    response = client.get("/visualize?repo=exampleorg/sample-repo")
    assert response.status_code == 200
    assert b"Interactive Visualizations" in response.data