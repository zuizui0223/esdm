from types import SimpleNamespace

from esdm.validate.v07i_gate import evaluate_v07i_gate


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=48,
        selected_lower_worst_sd_rate=0.8125,
        mean_worst_sd_ratio=0.82,
        minimum_worst_sd_ratio=0.60,
        maximum_worst_sd_ratio=1.05,
        mean_pilot_predicted_sd_ratio=0.75,
        oracle_placement_selection_rate=0.50,
        selection_counts={"2,6,7,8": 8, "1,5,7,8": 8},
        selected_mean_biases={
            "sp.suitability.alpha": 0.01,
            "sp.occupancy.psi0_logit": 0.03,
            "sp.occupancy.gamma_logit": -0.02,
            "sp.occupancy.epsilon_logit": 0.04,
        },
        selected_coverages={
            "sp.suitability.alpha": 0.875,
            "sp.occupancy.psi0_logit": 0.875,
            "sp.occupancy.gamma_logit": 0.875,
            "sp.occupancy.epsilon_logit": 0.875,
        },
        positive_heldout_gain_rate=0.50,
        mean_heldout_gain=0.0,
        minimum_heldout_gain=-0.2,
        total_divergences=0,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_v07i_gate_accepts_useful_burned_pilot_selection():
    decision = evaluate_v07i_gate(_summary())

    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07i_gate_requires_confirmatory_precision_gain_not_prediction_gain():
    decision = evaluate_v07i_gate(
        _summary(
            positive_heldout_gain_rate=0.0,
            mean_heldout_gain=-1.0,
        )
    )
    assert decision.passed

    assert not evaluate_v07i_gate(
        _summary(selected_lower_worst_sd_rate=0.6875)
    ).passed
    assert not evaluate_v07i_gate(
        _summary(mean_worst_sd_ratio=0.91)
    ).passed


def test_v07i_gate_counts_pilot_and_confirmatory_fits():
    assert not evaluate_v07i_gate(
        _summary(fit_count=32)
    ).passed
