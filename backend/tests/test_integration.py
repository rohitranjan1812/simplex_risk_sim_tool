"""Integration test for actuarial and CAT features via API."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module", name="api_client")
def _api_client() -> TestClient:
    return TestClient(app)


def test_api_with_actuarial_layers(api_client: TestClient):
    """Test API simulation endpoint with actuarial layers."""
    payload = {
        "trials": 1000,
        "seed": 42,
        "meta": {
            "portfolio_value": 5_000_000,
            "horizon_months": 12,
            "label": "Actuarial Test",
        },
        "factors": [
            {
                "name": "Property Loss",
                "frequency": 0.5,
                "severity_mean": 200_000,
                "severity_std": 100_000,
                "distribution": "lognormal",
            }
        ],
        "layers": [
            {
                "deductible": 50_000,
                "limit": 1_000_000,
                "participation": 0.8,
                "premium_rate": 0.02,
            }
        ],
    }
    
    response = api_client.post("/simulate", json=payload)
    assert response.status_code == 200
    
    body = response.json()
    
    # Check basic metrics
    assert body["mean_loss"] > 0
    assert body["loss_std"] > 0
    
    # Check actuarial metrics
    assert body["burning_cost"] is not None
    assert body["burning_cost"] > 0
    assert body["loss_ratio"] is not None
    assert body["layer_losses"] is not None
    assert "layer_0" in body["layer_losses"]
    assert body["net_retained_loss"] is not None
    
    # CAT metrics should be None (no CAT events)
    assert body["cat_event_count"] is None
    assert body["oep_curve"] is None
    assert body["pml_values"] is None


def test_api_with_cat_events(api_client: TestClient):
    """Test API simulation endpoint with CAT events."""
    payload = {
        "trials": 2000,
        "seed": 123,
        "meta": {
            "portfolio_value": 20_000_000,
            "horizon_months": 12,
            "label": "CAT Test",
        },
        "factors": [
            {
                "name": "Hurricane",
                "frequency": 0.1,
                "severity_mean": 5_000_000,
                "severity_std": 2_000_000,
                "distribution": "pareto",
                "is_cat_event": True,
                "geographic_zone": "Florida",
            },
            {
                "name": "Flood",
                "frequency": 0.15,
                "severity_mean": 3_000_000,
                "severity_std": 1_500_000,
                "distribution": "pareto",
                "is_cat_event": True,
                "geographic_zone": "Texas",
            },
        ],
    }
    
    response = api_client.post("/simulate", json=payload)
    assert response.status_code == 200
    
    body = response.json()
    
    # Check CAT metrics
    assert body["cat_event_count"] is not None
    assert body["cat_event_count"] >= 0
    assert body["oep_curve"] is not None
    assert len(body["oep_curve"]) > 0
    assert body["aep_curve"] is not None
    assert len(body["aep_curve"]) > 0
    assert body["pml_values"] is not None
    assert "pml_100y" in body["pml_values"]
    assert "pml_250y" in body["pml_values"]
    assert "pml_500y" in body["pml_values"]
    
    # Check geographic exposure
    assert body["geographic_exposure"] is not None
    assert "Florida" in body["geographic_exposure"]
    assert "Texas" in body["geographic_exposure"]


def test_api_with_combined_features(api_client: TestClient):
    """Test API with both actuarial layers and CAT events."""
    payload = {
        "trials": 3000,
        "seed": 456,
        "meta": {
            "portfolio_value": 15_000_000,
            "horizon_months": 12,
            "label": "Combined Test",
        },
        "factors": [
            {
                "name": "Regular Risk",
                "frequency": 1.0,
                "severity_mean": 100_000,
                "severity_std": 50_000,
                "distribution": "lognormal",
                "geographic_zone": "Global",
            },
            {
                "name": "Earthquake",
                "frequency": 0.02,
                "severity_mean": 10_000_000,
                "severity_std": 5_000_000,
                "distribution": "pareto",
                "is_cat_event": True,
                "geographic_zone": "California",
            },
        ],
        "layers": [
            {
                "deductible": 100_000,
                "limit": 5_000_000,
                "participation": 0.75,
                "premium_rate": 0.025,
            }
        ],
    }
    
    response = api_client.post("/simulate", json=payload)
    assert response.status_code == 200
    
    body = response.json()
    
    # Should have both actuarial and CAT metrics
    assert body["burning_cost"] is not None
    assert body["loss_ratio"] is not None
    assert body["layer_losses"] is not None
    assert body["net_retained_loss"] is not None
    
    assert body["cat_event_count"] is not None
    assert body["oep_curve"] is not None
    assert body["pml_values"] is not None
    assert body["geographic_exposure"] is not None
    
    # Verify return periods in OEP curve are sorted
    oep_levels = [point["level"] for point in body["oep_curve"]]
    assert oep_levels == sorted(oep_levels)
    
    # Verify PML values increase with return period
    assert body["pml_values"]["pml_100y"] <= body["pml_values"]["pml_250y"]
    assert body["pml_values"]["pml_250y"] <= body["pml_values"]["pml_500y"]
