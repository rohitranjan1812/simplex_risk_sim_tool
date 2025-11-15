"""Unit tests for the Monte Carlo engine."""
from app.sample_data import sample_request
from app.simulation import run_simulation


def test_run_simulation_generates_positive_losses():
    payload = sample_request()
    payload.trials = 2000
    result = run_simulation(payload)

    assert result.mean_loss > 0
    assert result.loss_max >= result.loss_min
    assert len(result.var) == 2
    assert len(result.histogram) > 0


def test_run_simulation_is_repeatable_with_seed():
    payload = sample_request()
    payload.trials = 1000
    payload.seed = 42

    first = run_simulation(payload)
    second = run_simulation(payload)

    assert first.mean_loss == second.mean_loss
    assert first.worst_trials == second.worst_trials
