from types import SimpleNamespace


def _qualification():
    return SimpleNamespace(
        interaction_structural_pass=True,
        interaction_practical_pass=True,
        null_structural_pass=True,
        null_practical_pass=True,
    )


def _summary():
    from esdm.validate.v05a_run import V05ASummary, V05AWorldSummary

    return V05ASummary(
        worlds={
            "interaction": V05AWorldSummary(
                world="interaction",
                replicates=16,
                mean_bias=0.02,
                coverage=0.875,
                nonzero_interval_rate=0.875,
                positive_interval_rate=0.875,
                heldout_positive_gain_rate=0.875,
                heldout_material_gain_rate=0.75,
                mean_heldout_gain=0.02,
                total_divergences=0,
            ),
            "measured_shared_null": V05AWorldSummary(
                world="measured_shared_null",
                replicates=16,
                mean_bias=0.01,
                coverage=0.875,
                nonzero_interval_rate=0.125,
                positive_interval_rate=0.0625,
                heldout_positive_gain_rate=0.5,
                heldout_material_gain_rate=0.125,
                mean_heldout_gain=0.0,
                total_divergences=0,
            ),
        },
        total_fits=64,
        total_divergences=0,
    )


def test_v05a_gate_requires_positive_recovery_and_null_refusal():
    from esdm.validate.v05a_gate import evaluate_v05a_gate

    decision = evaluate_v05a_gate(_qualification(), _summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)
