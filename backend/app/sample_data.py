"""Utility helpers for demo payloads."""
from .schemas import LossDistribution, RiskFactor, ScenarioMeta, SimulationRequest


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
            ),
            RiskFactor(
                name="Cyber breach",
                frequency=0.6,
                severity_mean=450_000,
                severity_std=200_000,
                distribution=LossDistribution.PARETO,
            ),
            RiskFactor(
                name="Weather outage",
                frequency=0.8,
                severity_mean=120_000,
                severity_std=80_000,
                distribution=LossDistribution.NORMAL,
            ),
        ],
    )
