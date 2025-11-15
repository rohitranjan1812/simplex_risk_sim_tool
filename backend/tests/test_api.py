"""API contract tests using FastAPI's test client."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sample_data import sample_request


@pytest.fixture(scope="module", name="api_client")
def _api_client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(api_client: TestClient):
    response = api_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_version"] == "0.1.0"


def test_simulate_endpoint(api_client: TestClient):
    payload = sample_request().model_dump()
    response = api_client.post("/simulate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["mean_loss"] > 0
    assert len(body["var"]) == 2


def test_sample_scenario_endpoint(api_client: TestClient):
    response = api_client.get("/scenarios/sample")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["label"] == "Global Base Case"
