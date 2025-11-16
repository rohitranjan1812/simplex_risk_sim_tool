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
    is_cat_event: bool = Field(False, description="Whether this is a catastrophic event (rare, high severity).")
    geographic_zone: str | None = Field(None, max_length=50, description="Geographic zone for spatial correlation.")


class ActuarialLayer(BaseModel):
    """Represents an insurance layer with deductible and limit."""

    deductible: float = Field(0.0, ge=0.0, description="Attachment point (deductible) for this layer.")
    limit: float | None = Field(None, gt=0.0, description="Maximum coverage limit for this layer.")
    participation: Annotated[float, confloat(gt=0.0, le=1.0)] = Field(
        1.0, description="Coinsurance/participation rate (0-1)."
    )
    premium_rate: Annotated[float, confloat(ge=0.0, le=1.0)] | None = Field(
        None, description="Premium rate as fraction of expected losses."
    )


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
    layers: list[ActuarialLayer] = Field(
        default_factory=list, description="Insurance layers for actuarial analysis."
    )

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
    # Actuarial metrics
    burning_cost: float | None = Field(None, description="Average annual loss rate.")
    loss_ratio: float | None = Field(None, description="Loss ratio for actuarial pricing.")
    layer_losses: dict[str, float] | None = Field(None, description="Losses by layer after deductibles/limits.")
    net_retained_loss: float | None = Field(None, description="Net loss after applying layers.")
    # CAT metrics
    oep_curve: list[PercentilePoint] | None = Field(None, description="Occurrence Exceedance Probability curve.")
    aep_curve: list[PercentilePoint] | None = Field(None, description="Aggregate Exceedance Probability curve.")
    pml_values: dict[str, float] | None = Field(None, description="Probable Maximum Loss at various return periods.")
    cat_event_count: int | None = Field(None, description="Number of catastrophic events in simulation.")
    geographic_exposure: dict[str, float] | None = Field(
        None, description="Exposure breakdown by geographic zone."
    )


class HealthResponse(BaseModel):
    """Simple health response."""

    status: str = "ok"
    api_version: str
