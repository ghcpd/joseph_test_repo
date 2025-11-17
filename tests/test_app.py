import os
import sys

import pytest

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, data_store


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"PR & Issue Dashboard" in response.data
    assert b"Merged Data" in response.data


def test_dataset_detail_page(client):
    merged_records = data_store.get_dataset("merged_data")
    assert merged_records, "Merged data should not be empty for tests"
    record_id = merged_records[0]["_record_id"]
    response = client.get(f"/dataset/merged_data/{record_id}")
    assert response.status_code == 200
    assert bytes(str(record_id), "utf-8") in response.data


def test_api_filtering(client):
    response = client.get("/api/merged_data?repo=example/repo-one")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data, "Expected filtered data"
    for entry in data:
        assert entry.get("repo") == "example/repo-one"


def test_visualize_page(client):
    response = client.get("/visualize")
    assert response.status_code == 200
    assert b"Top Repositories by PR Count" in response.data