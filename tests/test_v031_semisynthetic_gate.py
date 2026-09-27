import importlib.util
import math

import pytest

from esdm.validate.v031_semisynthetic_gate import (
    V031SemiSyntheticGateConfig,
    V031SemiSyntheticReplicate,
    evaluate_v031_semisynthetic_gate,
    summarize_v031_semisynthetic,
)


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def _passing_records():
    rows = []
    for i in range(20):
        rows.append(
            V031SemiSyntheticReplicate(
                replicate=i,
                beta_precip_mean=0.55 + (0.03 if i % 2 else -0.03),
                beta_precip_low=0.30,
                beta_precip_high=0.80,
                beta_lat_mean=-0.25 + (0.02 if i % 2 else -0.02),
                beta_lat_low=-0.50,
                beta_lat_high=0.02,
                full_heldout_log_score=-1.10,
                knockout_heldout_log_score=-1.14,
                full_divergences=0,
                knockout_divergences=0,
            )
        )
    return tuple(rows)


def test_gate_f_summary_and_decision_apply_frozen_thresholds():
    summary = summarize_v031_semisynthetic(_passing_records())
    assert summary.replicates == 20
    assert summary.positive_gain_rate == 1.0
    assert math.isclose(summary.mean_heldout_gain, 0.04, abs_tol=1e-12)
    decision = evaluate_v031_semisynthetic_gate(
        summary,
        config=V031SemiSyntheticGateConfig(),
    )
    assert decision.passed


def test_gate_f_fails_transfer_even_if_parameter_recovery_is_good():
    rows = list(_passing_records())
    rows = [
        V031SemiSyntheticReplicate(
            replicate=row.replicate,
            beta_precip_mean=row.beta_precip_mean,
            beta_precip_low=row.beta_precip_low,
            beta_precip_high=row.beta_precip_high,
            beta_lat_mean=row.beta_lat_mean,
            beta_lat_low=row.beta_lat_low,
            beta_lat_high=row.beta_lat_high,
            full_heldout_log_score=-1.20,
            knockout_heldout_log_score=-1.14,
            full_divergences=0,
            knockout_divergences=0,
        )
        for row in rows
    ]
    decision = evaluate_v031_semisynthetic_gate(summarize_v031_semisynthetic(rows))
    assert not decision.passed
    checks = {check.name: check for check in decision.checks}
    assert not checks["heldout_positive_gain_rate"].passed
    assert not checks["heldout_mean_gain"].passed


def _sample_csv(rows=120):
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(rows):
        # Include west, central and east longitudes deterministically.
        longitude = (-130.0 if i % 3 == 0 else -95.0 if i % 3 == 1 else -75.0)
        longitude += (i % 7) * 0.3
        latitude = 24.0 + (i % 35) * 0.6
        average = 38.0 + (i % 19) * 1.8
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.1f},{latitude:.4f},{longitude:.4f},ST,50.0"
        )
    return "\n".join(lines) + "\n"


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_gate_f_runner_smoke_fits_train_and_scores_heldout():
    from esdm.validate.v031_semisynthetic_gate import run_v031_semisynthetic_benchmark

    result = run_v031_semisynthetic_benchmark(
        _sample_csv(),
        replicates=1,
        base_seed=91,
        num_warmup=30,
        num_samples=40,
        num_chains=1,
        progress_bar=False,
    )
    assert result.summary.replicates == 1
    assert len(result.replicates) == 1
    row = result.replicates[0]
    assert math.isfinite(row.full_heldout_log_score)
    assert math.isfinite(row.knockout_heldout_log_score)
