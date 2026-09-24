from esdm.validate.v05b_run import V05BSummary


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        mean_beta=0.02,
        zero_coverage=0.875,
        nonzero_interval_rate=0.125,
        heldout_positive_gain_rate=0.5,
        heldout_material_gain_rate=0.125,
        mean_heldout_gain=-0.01,
        total_divergences=0,
    )
    values.update(overrides)
    return V05BSummary(**values)


def test_v05b_gate_requires_hidden_driver_refusal():
    from esdm.validate.v05b_gate import evaluate_v05b_gate

    assert evaluate_v05b_gate(_summary()).passed is True
    assert evaluate_v05b_gate(_summary(mean_beta=0.15)).passed is False
    assert evaluate_v05b_gate(
        _summary(heldout_material_gain_rate=0.3125)
    ).passed is False
