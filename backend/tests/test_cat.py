"""Tests for CAT/accumulation features."""
import pytest

from app.schemas import (
    LossDistribution,
    RiskFactor,
    ScenarioMeta,
    SimulationRequest,
)
from app.simulation import run_simulation


def test_cat_event_identification():
    """Test that CAT events are properly identified and counted."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=10_000_000,
            horizon_months=12,
            label="CAT Event Test",
        ),
        factors=[
            RiskFactor(
                name="Earthquake",
                frequency=0.1,  # Rare event
                severity_mean=5_000_000,
                severity_std=2_000_000,
                distribution=LossDistribution.PARETO,
                is_cat_event=True,
            ),
            RiskFactor(
                name="Regular Risk",
                frequency=1.0,
                severity_mean=50_000,
                severity_std=20_000,
                distribution=LossDistribution.LOGNORMAL,
                is_cat_event=False,
            ),
        ],
    )
    
    result = run_simulation(payload)
    
    # CAT metrics should be calculated
    assert result.cat_event_count is not None
    assert result.oep_curve is not None
    assert result.aep_curve is not None
    assert result.pml_values is not None
    
    # OEP curve should have multiple return periods
    assert len(result.oep_curve) > 0
    # Return periods should be in ascending order
    return_periods = [point.level for point in result.oep_curve]
    assert return_periods == sorted(return_periods)


def test_oep_aep_curves():
    """Test that OEP and AEP curves are correctly calculated."""
    payload = SimulationRequest(
        trials=5000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=10_000_000,
            horizon_months=12,
            label="OEP/AEP Test",
        ),
        factors=[
            RiskFactor(
                name="Hurricane",
                frequency=0.2,
                severity_mean=3_000_000,
                severity_std=1_500_000,
                distribution=LossDistribution.PARETO,
                is_cat_event=True,
            ),
        ],
    )
    
    result = run_simulation(payload)
    
    # Both curves should exist
    assert result.oep_curve is not None
    assert result.aep_curve is not None
    
    # Values should increase with return period
    oep_values = [point.value for point in result.oep_curve]
    for i in range(len(oep_values) - 1):
        # Higher return period should have higher loss
        assert oep_values[i] <= oep_values[i + 1]


def test_pml_calculation():
    """Test that PML values are calculated at standard return periods."""
    payload = SimulationRequest(
        trials=5000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=20_000_000,
            horizon_months=12,
            label="PML Test",
        ),
        factors=[
            RiskFactor(
                name="Wildfire",
                frequency=0.15,
                severity_mean=4_000_000,
                severity_std=2_000_000,
                distribution=LossDistribution.PARETO,
                is_cat_event=True,
            ),
        ],
    )
    
    result = run_simulation(payload)
    
    assert result.pml_values is not None
    
    # Standard return periods should be present
    assert "pml_100y" in result.pml_values
    assert "pml_250y" in result.pml_values
    assert "pml_500y" in result.pml_values
    
    # PML values should increase with return period
    assert result.pml_values["pml_100y"] <= result.pml_values["pml_250y"]
    assert result.pml_values["pml_250y"] <= result.pml_values["pml_500y"]


def test_geographic_exposure_tracking():
    """Test that geographic exposure is tracked by zone."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=10_000_000,
            horizon_months=12,
            label="Geographic Test",
        ),
        factors=[
            RiskFactor(
                name="California Earthquake",
                frequency=0.1,
                severity_mean=2_000_000,
                severity_std=1_000_000,
                distribution=LossDistribution.PARETO,
                is_cat_event=False,
                geographic_zone="California",
            ),
            RiskFactor(
                name="Florida Hurricane",
                frequency=0.3,
                severity_mean=1_500_000,
                severity_std=800_000,
                distribution=LossDistribution.PARETO,
                is_cat_event=False,
                geographic_zone="Florida",
            ),
            RiskFactor(
                name="Texas Storm",
                frequency=0.5,
                severity_mean=500_000,
                severity_std=300_000,
                distribution=LossDistribution.LOGNORMAL,
                is_cat_event=False,
                geographic_zone="Texas",
            ),
        ],
    )
    
    result = run_simulation(payload)
    
    # Geographic exposure should be tracked
    assert result.geographic_exposure is not None
    assert "California" in result.geographic_exposure
    assert "Florida" in result.geographic_exposure
    assert "Texas" in result.geographic_exposure
    
    # Each zone should have positive exposure
    assert result.geographic_exposure["California"] > 0
    assert result.geographic_exposure["Florida"] > 0
    assert result.geographic_exposure["Texas"] > 0


def test_non_cat_events_no_cat_metrics():
    """Test that non-CAT simulations don't calculate CAT metrics."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=5_000_000,
            horizon_months=12,
            label="Non-CAT Test",
        ),
        factors=[
            RiskFactor(
                name="Regular Risk",
                frequency=1.0,
                severity_mean=100_000,
                severity_std=50_000,
                distribution=LossDistribution.LOGNORMAL,
                is_cat_event=False,
            ),
        ],
    )
    
    result = run_simulation(payload)
    
    # CAT-specific metrics should be None
    assert result.cat_event_count is None
    assert result.oep_curve is None
    assert result.aep_curve is None
    assert result.pml_values is None


def test_combined_cat_and_regular_risks():
    """Test simulation with both CAT and regular risk factors."""
    payload = SimulationRequest(
        trials=2000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=15_000_000,
            horizon_months=12,
            label="Mixed Risk Test",
        ),
        factors=[
            RiskFactor(
                name="Catastrophic Event",
                frequency=0.05,
                severity_mean=8_000_000,
                severity_std=3_000_000,
                distribution=LossDistribution.PARETO,
                is_cat_event=True,
                geographic_zone="West Coast",
            ),
            RiskFactor(
                name="Operational Loss",
                frequency=2.0,
                severity_mean=50_000,
                severity_std=25_000,
                distribution=LossDistribution.LOGNORMAL,
                is_cat_event=False,
                geographic_zone="East Coast",
            ),
        ],
    )
    
    result = run_simulation(payload)
    
    # Should have all metrics
    assert result.mean_loss > 0
    assert result.burning_cost is not None
    
    # CAT metrics should be present
    assert result.cat_event_count is not None
    assert result.oep_curve is not None
    assert result.pml_values is not None
    
    # Geographic exposure for both zones
    assert result.geographic_exposure is not None
    assert "West Coast" in result.geographic_exposure
    assert "East Coast" in result.geographic_exposure
