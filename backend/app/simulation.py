"""Core Monte Carlo routines for the risk simulation API."""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from .config import get_settings
from .schemas import (
    ActuarialLayer,
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


def _simulate_losses(rng: np.random.Generator, factors: Iterable[RiskFactor], trials: int) -> tuple[np.ndarray, dict]:
    """Simulate losses and track additional CAT metrics."""
    total_losses = np.zeros(trials, dtype=float)
    cat_event_counts = np.zeros(trials, dtype=int)
    geographic_losses = {}
    
    for factor in factors:
        counts = rng.poisson(lam=factor.frequency, size=trials)
        if not np.any(counts):
            continue
        severity = _sample_severity(rng, factor, trials)
        factor_losses = counts * severity
        total_losses += factor_losses
        
        # Track CAT events
        if factor.is_cat_event:
            cat_event_counts += counts
        
        # Track geographic exposure
        if factor.geographic_zone:
            if factor.geographic_zone not in geographic_losses:
                geographic_losses[factor.geographic_zone] = np.zeros(trials, dtype=float)
            geographic_losses[factor.geographic_zone] += factor_losses
    
    metrics = {
        "cat_event_counts": cat_event_counts,
        "geographic_losses": geographic_losses,
    }
    return total_losses, metrics


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


def _apply_layers(gross_losses: np.ndarray, layers: list[ActuarialLayer]) -> tuple[np.ndarray, dict[str, float]]:
    """Apply actuarial layers (deductibles, limits, participation) to gross losses."""
    if not layers:
        return gross_losses, {}
    
    net_losses = gross_losses.copy()
    layer_losses = {}
    
    for idx, layer in enumerate(layers):
        layer_name = f"layer_{idx}"
        
        # Apply deductible
        excess = np.maximum(gross_losses - layer.deductible, 0.0)
        
        # Apply limit
        if layer.limit is not None:
            capped = np.minimum(excess, layer.limit)
        else:
            capped = excess
        
        # Apply participation/coinsurance
        layer_covered = capped * layer.participation
        layer_losses[layer_name] = float(np.mean(layer_covered))
        
        # Net retained loss after this layer
        net_losses = gross_losses - layer_covered
    
    return net_losses, layer_losses


def _calculate_oep_curve(losses: np.ndarray, return_periods: list[int] = None) -> list[PercentilePoint]:
    """Calculate Occurrence Exceedance Probability curve for CAT events."""
    if return_periods is None:
        return_periods = [10, 25, 50, 100, 250, 500]
    
    oep_curve = []
    for rp in return_periods:
        # OEP at return period N means 1/N annual exceedance probability
        exceedance_prob = 1.0 / rp
        percentile = 1.0 - exceedance_prob
        if percentile < 1.0:
            value = float(np.quantile(losses, percentile))
            oep_curve.append(PercentilePoint(level=rp, value=value))
    
    return oep_curve


def _calculate_aep_curve(losses: np.ndarray, return_periods: list[int] = None) -> list[PercentilePoint]:
    """Calculate Aggregate Exceedance Probability curve."""
    if return_periods is None:
        return_periods = [10, 25, 50, 100, 250, 500]
    
    # AEP considers cumulative annual losses
    aep_curve = []
    for rp in return_periods:
        exceedance_prob = 1.0 / rp
        percentile = 1.0 - exceedance_prob
        if percentile < 1.0:
            value = float(np.quantile(losses, percentile))
            aep_curve.append(PercentilePoint(level=rp, value=value))
    
    return aep_curve


def _calculate_pml(losses: np.ndarray, return_periods: list[int] = None) -> dict[str, float]:
    """Calculate Probable Maximum Loss at various return periods."""
    if return_periods is None:
        return_periods = [100, 250, 500]
    
    pml_values = {}
    for rp in return_periods:
        exceedance_prob = 1.0 / rp
        percentile = 1.0 - exceedance_prob
        if percentile < 1.0:
            pml_values[f"pml_{rp}y"] = float(np.quantile(losses, percentile))
    
    return pml_values


def run_simulation(payload: SimulationRequest) -> SimulationResult:
    settings = get_settings()
    trials = min(payload.trials, settings.max_trials)
    rng = np.random.default_rng(payload.seed)
    losses, cat_metrics = _simulate_losses(rng, payload.factors, trials)
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

    # Actuarial calculations
    burning_cost = summary["mean"] / metadata.portfolio_value if metadata.portfolio_value > 0 else 0.0
    loss_ratio = None
    layer_losses = None
    net_retained_loss = None
    
    if payload.layers:
        net_losses, layer_losses = _apply_layers(losses, payload.layers)
        net_retained_loss = float(np.mean(net_losses))
        
        # Calculate loss ratio if premium rate is specified
        total_premium = sum(
            layer.premium_rate * metadata.portfolio_value 
            for layer in payload.layers 
            if layer.premium_rate is not None
        )
        if total_premium > 0:
            total_layer_loss = sum(layer_losses.values())
            loss_ratio = total_layer_loss / total_premium

    # CAT metrics
    cat_event_count = None
    geographic_exposure = None
    oep_curve = None
    aep_curve = None
    pml_values = None
    
    # Check if any factors are CAT events
    has_cat_events = any(f.is_cat_event for f in payload.factors)
    has_geographic = any(f.geographic_zone for f in payload.factors)
    
    if has_cat_events:
        cat_event_count = int(np.sum(cat_metrics["cat_event_counts"] > 0))
        oep_curve = _calculate_oep_curve(losses)
        aep_curve = _calculate_aep_curve(losses)
        pml_values = _calculate_pml(losses)
    
    if has_geographic and cat_metrics["geographic_losses"]:
        geographic_exposure = {
            zone: float(np.mean(zone_losses))
            for zone, zone_losses in cat_metrics["geographic_losses"].items()
        }

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
        burning_cost=burning_cost,
        loss_ratio=loss_ratio,
        layer_losses=layer_losses,
        net_retained_loss=net_retained_loss,
        oep_curve=oep_curve,
        aep_curve=aep_curve,
        pml_values=pml_values,
        cat_event_count=cat_event_count,
        geographic_exposure=geographic_exposure,
    )
