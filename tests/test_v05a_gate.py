from esdm.validate.v05a_gate import V05AIdentificationSummary
from esdm.validate.v05a_run import V05ASummary, V05AWorldSummary


def _identification():
    return V05AIdentificationSummary(
        directed_structural=True,
        directed_practical=True,
        null_structural=True,
        null_practical=True,
        directed_target_sd=0.1,
        null_target_sd=0.1,
    )


def _world(name, *, mean_beta, mean_bias, coverage, nonzero, positive_gain, material_gain, mean_gain):
    return V05AWorldSummary(
        world=name,
        replicates=16,
        mean_beta=mean_beta,
        mean_bias=mean_bias,
        truth_coverage=coverage,
        nonzero_rate=nonzero,
        positive_gain_rate=positive_gain,
        material_gain_rate=material_gain,
        mean_heldout_gain=mean_gain,
        total_divergences=0,
    )


def _summary():
    return V05ASummary(
        worlds={
            "directed_positive": _world(
                "directed_positive",
                mean_beta=0.8,
                mean_bias=0.0,
                coverage=0.9,
                nonzero=1.0,
                positive_gain=0.9,
                material_gain=0.8,
                mean_gain=0.02,
            ),
            "interaction_null": _world(
                "interaction_null",
                mean_beta=0.01,
                mean_bias=0.01,
                coverage=0.9,
                nonzero=0.1,
                positive_gain=0.5,
                material_gain=0.1,
                mean_gain=0.0,
            ),
        },
        fit_count=64,
        total_divergences=0,
        extrapolation_integrity=True,
    )


def test_v05a_gate_accepts_directed_signal_and_null_refusal():
    from esdm.validate.v05a_gate import evaluate_v05a_gate

    decision = evaluate_v05a_gate(_identification(), _summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)
