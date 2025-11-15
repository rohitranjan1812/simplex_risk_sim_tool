"""Pydantic schemas used by the FastAPI service."""
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, PositiveFloat, confloat, conint


class LossDistribution(str, Enum):
    """Supported loss severity distributions."""

    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    PARETO = "pareto"


class RiskFactor(BaseModel):
    """Represents a single independent risk factor."""

    name: str = Field(..., min_length=2, max_length=60)
    frequency: PositiveFloat = Field(
        ..., description="Expected number of loss events per period (Poisson lambda)."
    )
    severity_mean: PositiveFloat = Field(..., description="Mean loss severity per event.")
    severity_std: PositiveFloat = Field(..., description="Std deviation of loss severity per event.")
    distribution: LossDistribution = LossDistribution.LOGNORMAL
    correlation: Annotated[float, confloat(ge=-0.95, le=0.95)] = 0.0


class ScenarioMeta(BaseModel):
    """Metadata describing fixed scenario inputs."""

    portfolio_value: PositiveFloat = Field(..., description="Total value exposed to risk.")
    horizon_months: Annotated[int, conint(ge=1, le=60)] = 12
    label: str = Field("Base Case", max_length=80)


class SimulationRequest(BaseModel):
    """Incoming payload to run Monte Carlo."""

    trials: Annotated[int, conint(ge=100, le=500_000)] = 10_000
    seed: int | None = Field(None, description="Optional RNG seed for reproducibility.")
    meta: ScenarioMeta
    factors: list[RiskFactor]

    model_config = {
        "json_schema_extra": {
            "example": {
                "trials": 5000,
                "seed": 123,
                "meta": {
                    "portfolio_value": 5_000_000,
                    "horizon_months": 12,
                    "label": "North America ops",
                },
                "factors": [
                    {
                        "name": "Supply disruption",
                        "frequency": 0.3,
                        "severity_mean": 250_000,
                        "severity_std": 100_000,
                        "distribution": "lognormal",
                    },
                    {
                        "name": "Cyber breach",
                        "frequency": 0.5,
                        "severity_mean": 400_000,
                        "severity_std": 150_000,
                        "distribution": "pareto",
                    },
                ],
            }
        }
    }


class PercentilePoint(BaseModel):
    """Holds point estimates for VaR-like stats."""

    level: float
    value: float


class HistogramBucket(BaseModel):
    """Simple histogram bucket for the UI."""

    start: float
    end: float
    probability: float


class SimulationResult(BaseModel):
    """Response returned to clients."""

    mean_loss: float
    loss_std: float
    loss_min: float
    loss_max: float
    var: list[PercentilePoint]
    cvar: list[PercentilePoint]
    histogram: list[HistogramBucket]
    worst_trials: list[float]
    expected_shortfall: float
    probability_of_loss: float
    metadata: ScenarioMeta


class HealthResponse(BaseModel):
    """Simple health response."""

    status: str = "ok"
    api_version: str
