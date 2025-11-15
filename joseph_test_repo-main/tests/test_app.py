import pytest

from app import app, DATASETS


@pytest.fixture()
def client():
    return app.test_client()


def test_home_page_status(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"PR Issue Search Results" in response.data


def test_api_dataset_count(client):
    response = client.get("/api/merged_data")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] == DATASETS["merged_data"]["count"]
    assert len(payload["data"]) == DATASETS["merged_data"]["count"]


def test_dataset_detail_page(client):
    dataset_name = "merged_data"
    record_id = next(iter(DATASETS[dataset_name]["index"].keys()))
    response = client.get(f"/dataset/{dataset_name}/{record_id}")
    assert response.status_code == 200
    assert record_id.encode() in response.data