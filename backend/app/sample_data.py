"""Utility helpers for demo payloads."""
from .schemas import ActuarialLayer, LossDistribution, RiskFactor, ScenarioMeta, SimulationRequest


def sample_request() -> SimulationRequest:
    return SimulationRequest(
        trials=5000,
        seed=7,
        meta=ScenarioMeta(
            portfolio_value=12_000_000,
            horizon_months=12,
            label="Global Base Case",
        ),
        factors=[
            RiskFactor(
                name="Supply disruption",
                frequency=0.4,
                severity_mean=280_000,
                severity_std=150_000,
                distribution=LossDistribution.LOGNORMAL,
                geographic_zone="Asia Pacific",
            ),
            RiskFactor(
                name="Cyber breach",
                frequency=0.6,
                severity_mean=450_000,
                severity_std=200_000,
                distribution=LossDistribution.PARETO,
                geographic_zone="North America",
            ),
            RiskFactor(
                name="Weather outage",
                frequency=0.8,
                severity_mean=120_000,
                severity_std=80_000,
                distribution=LossDistribution.NORMAL,
                geographic_zone="Europe",
            ),
            RiskFactor(
                name="Hurricane (CAT)",
                frequency=0.05,
                severity_mean=3_500_000,
                severity_std=1_800_000,
                distribution=LossDistribution.PARETO,
                is_cat_event=True,
                geographic_zone="Gulf Coast",
            ),
        ],
        layers=[
            ActuarialLayer(
                deductible=100_000,
                limit=2_000_000,
                participation=0.8,
                premium_rate=0.015,
            )
        ],
    )
