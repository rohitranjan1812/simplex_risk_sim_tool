"""Core Monte Carlo routines for the risk simulation API."""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from .config import get_settings
from .schemas import (
    HistogramBucket,
    LossDistribution,
    PercentilePoint,
    RiskFactor,
    ScenarioMeta,
    SimulationRequest,
    SimulationResult,
)


def _lognormal_params(mean: float, std: float) -> tuple[float, float]:
    variance_ratio = (std / mean) ** 2
    sigma2 = math.log1p(variance_ratio)
    return math.log(mean) - 0.5 * sigma2, math.sqrt(sigma2)


def _sample_severity(rng: np.random.Generator, factor: RiskFactor, trials: int) -> np.ndarray:
    if factor.distribution == LossDistribution.NORMAL:
        samples = rng.normal(factor.severity_mean, factor.severity_std, size=trials)
        return np.clip(samples, 0.0, None)

    if factor.distribution == LossDistribution.LOGNORMAL:
        mu, sigma = _lognormal_params(factor.severity_mean, factor.severity_std)
        return rng.lognormal(mean=mu, sigma=sigma, size=trials)

    # Pareto tail, fall back to heuristic alpha derived from coefficient of variation.
    coeff = factor.severity_std / factor.severity_mean
    alpha = np.clip(1.5 + (1.0 / max(coeff, 1e-3)), 1.8, 6.0)
    scale = factor.severity_mean * (alpha - 1) / alpha
    return (rng.pareto(alpha, trials) + 1.0) * scale


def _simulate_losses(rng: np.random.Generator, factors: Iterable[RiskFactor], trials: int) -> np.ndarray:
    total_losses = np.zeros(trials, dtype=float)
    for factor in factors:
        counts = rng.poisson(lam=factor.frequency, size=trials)
        if not np.any(counts):
            continue
        severity = _sample_severity(rng, factor, trials)
        total_losses += counts * severity
    return total_losses


def _build_histogram(losses: np.ndarray, buckets: int = 20) -> list[HistogramBucket]:
    if not len(losses):
        return []
    counts, edges = np.histogram(losses, bins=buckets, density=True)
    hist = []
    for idx, prob in enumerate(counts):
        hist.append(
            HistogramBucket(
                start=float(edges[idx]),
                end=float(edges[idx + 1]),
                probability=float(prob * (edges[idx + 1] - edges[idx])),
            )
        )
    return hist


def _percentiles(losses: np.ndarray, levels: Iterable[float]) -> list[PercentilePoint]:
    return [
        PercentilePoint(level=level, value=float(np.quantile(losses, level))) for level in levels
    ]


def _cvar(losses: np.ndarray, level: float) -> float:
    var_threshold = np.quantile(losses, level)
    tail = losses[losses >= var_threshold]
    if not len(tail):
        return float(var_threshold)
    return float(np.mean(tail))


def run_simulation(payload: SimulationRequest) -> SimulationResult:
    settings = get_settings()
    trials = min(payload.trials, settings.max_trials)
    rng = np.random.default_rng(payload.seed)
    losses = _simulate_losses(rng, payload.factors, trials)
    metadata: ScenarioMeta = payload.meta

    summary = {
        "mean": float(np.mean(losses)),
        "std": float(np.std(losses)),
        "min": float(np.min(losses)),
        "max": float(np.max(losses)),
    }
    conf_levels = settings.confidence_levels
    var_points = _percentiles(losses, conf_levels)
    cvar_points = [PercentilePoint(level=level, value=_cvar(losses, level)) for level in conf_levels]

    histogram = _build_histogram(losses)
    worst_trials = sorted(losses)[-10:]
    probability_of_loss = float(np.mean(losses > 0.0))
    expected_shortfall = float(np.mean(losses[losses > summary["mean"]])) if losses.any() else 0.0

    return SimulationResult(
        mean_loss=summary["mean"],
        loss_std=summary["std"],
        loss_min=summary["min"],
        loss_max=summary["max"],
        var=var_points,
        cvar=cvar_points,
        histogram=histogram,
        worst_trials=[float(x) for x in worst_trials[::-1]],
        expected_shortfall=expected_shortfall,
        probability_of_loss=probability_of_loss,
        metadata=metadata,
    )
