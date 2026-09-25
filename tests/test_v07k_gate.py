from types import SimpleNamespace

from esdm.validate.v07k_gate import evaluate_v07k_gate


def _world(**overrides):
    values = dict(
        replicates=16,
        fit_count=48,
        adaptive_lower_worst_sd_rate=0.8125,
        mean_worst_sd_ratio=0.90,
        minimum_ratio=0.6,
        maximum_ratio=1.1,
        mean_pilot_predicted_ratio=0.90,
        oracle_placement_selection_rate=0.5,
        selection_counts={"1,3,7,8": 8, "1,2,7,8": 8},
        adaptive_mean_biases={
            "sp.suitability.alpha": 0.01,
            "sp.occupancy.psi0_logit": 0.05,
            "sp.occupancy.gamma_logit": -0.04,
            "sp.occupancy.epsilon_logit": 0.08,
        },
        adaptive_coverages={
            "sp.suitability.alpha": 0.875,
            "sp.occupancy.psi0_logit": 0.875,
            "sp.occupancy.gamma_logit": 0.8125,
            "sp.occupancy.epsilon_logit": 0.8125,
        },
        positive_heldout_gain_rate=0.5,
        mean_heldout_gain=0.0,
        total_divergences=0,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _summary(**overrides):
    worlds = {
        "transfer_positive": _world(),
        "reversal": _world(),
    }
    values = dict(
        worlds=worlds,
        replicates=32,
        fit_count=96,
        total_divergences=0,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_v07k_gate_accepts_incremental_local_adaptation_gain():
    decision = evaluate_v07k_gate(_summary())

    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07k_gate_requires_precision_gain_in_each_shift_world():
    summary = _summary()
    summary.worlds["transfer_positive"] = _world(
        adaptive_lower_worst_sd_rate=0.6875
    )
    assert not evaluate_v07k_gate(summary).passed

    summary = _summary()
    summary.worlds["reversal"] = _world(mean_worst_sd_ratio=0.96)
    assert not evaluate_v07k_gate(summary).passed


def test_v07k_prediction_is_descriptive_only():
    summary = _summary()
    summary.worlds["transfer_positive"] = _world(
        positive_heldout_gain_rate=0.0,
        mean_heldout_gain=-1.0,
    )
    summary.worlds["reversal"] = _world(
        positive_heldout_gain_rate=0.0,
        mean_heldout_gain=-1.0,
    )

    assert evaluate_v07k_gate(summary).passed
