"""Tests for advanced actuarial features."""
import pytest

from app.schemas import (
    ActuarialLayer,
    LossDistribution,
    RiskFactor,
    ScenarioMeta,
    SimulationRequest,
)
from app.simulation import run_simulation


def test_burning_cost_calculation():
    """Test that burning cost is calculated correctly."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=10_000_000,
            horizon_months=12,
            label="Burning Cost Test",
        ),
        factors=[
            RiskFactor(
                name="Test Risk",
                frequency=0.5,
                severity_mean=100_000,
                severity_std=50_000,
                distribution=LossDistribution.LOGNORMAL,
            )
        ],
    )
    
    result = run_simulation(payload)
    
    # Burning cost should be mean_loss / portfolio_value
    expected_burning_cost = result.mean_loss / 10_000_000
    assert result.burning_cost is not None
    assert abs(result.burning_cost - expected_burning_cost) < 1e-6


def test_actuarial_layers_with_deductible():
    """Test that actuarial layers apply deductibles correctly."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=5_000_000,
            horizon_months=12,
            label="Layer Test",
        ),
        factors=[
            RiskFactor(
                name="Base Risk",
                frequency=1.0,
                severity_mean=200_000,
                severity_std=100_000,
                distribution=LossDistribution.LOGNORMAL,
            )
        ],
        layers=[
            ActuarialLayer(
                deductible=50_000,
                limit=500_000,
                participation=1.0,
            )
        ],
    )
    
    result = run_simulation(payload)
    
    # Layer losses should be calculated
    assert result.layer_losses is not None
    assert "layer_0" in result.layer_losses
    
    # Net retained loss should be different from mean loss
    assert result.net_retained_loss is not None
    assert result.net_retained_loss != result.mean_loss


def test_actuarial_layers_with_coinsurance():
    """Test that actuarial layers apply coinsurance correctly."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=5_000_000,
            horizon_months=12,
            label="Coinsurance Test",
        ),
        factors=[
            RiskFactor(
                name="Base Risk",
                frequency=1.0,
                severity_mean=200_000,
                severity_std=100_000,
                distribution=LossDistribution.LOGNORMAL,
            )
        ],
        layers=[
            ActuarialLayer(
                deductible=0,
                limit=1_000_000,
                participation=0.5,  # 50% coinsurance
            )
        ],
    )
    
    result = run_simulation(payload)
    
    # With 50% participation, layer should cover roughly half
    assert result.layer_losses is not None
    assert result.net_retained_loss is not None
    # Net retained should be roughly half of mean loss
    assert result.net_retained_loss > result.mean_loss * 0.3


def test_loss_ratio_with_premium():
    """Test that loss ratio is calculated when premium rate is provided."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=10_000_000,
            horizon_months=12,
            label="Loss Ratio Test",
        ),
        factors=[
            RiskFactor(
                name="Base Risk",
                frequency=0.5,
                severity_mean=100_000,
                severity_std=50_000,
                distribution=LossDistribution.LOGNORMAL,
            )
        ],
        layers=[
            ActuarialLayer(
                deductible=0,
                limit=1_000_000,
                participation=1.0,
                premium_rate=0.01,  # 1% of portfolio value
            )
        ],
    )
    
    result = run_simulation(payload)
    
    # Loss ratio should be calculated
    assert result.loss_ratio is not None
    # Loss ratio = layer_losses / premium
    expected_premium = 0.01 * 10_000_000
    expected_loss_ratio = result.layer_losses["layer_0"] / expected_premium
    assert abs(result.loss_ratio - expected_loss_ratio) < 1e-6


def test_no_layers_means_no_actuarial_metrics():
    """Test that without layers, layer-specific metrics are None."""
    payload = SimulationRequest(
        trials=1000,
        seed=42,
        meta=ScenarioMeta(
            portfolio_value=5_000_000,
            horizon_months=12,
            label="No Layers Test",
        ),
        factors=[
            RiskFactor(
                name="Base Risk",
                frequency=0.5,
                severity_mean=100_000,
                severity_std=50_000,
                distribution=LossDistribution.LOGNORMAL,
            )
        ],
    )
    
    result = run_simulation(payload)
    
    # Burning cost should still be calculated
    assert result.burning_cost is not None
    
    # But layer-specific metrics should be None
    assert result.layer_losses is None
    assert result.net_retained_loss is None
    assert result.loss_ratio is None
