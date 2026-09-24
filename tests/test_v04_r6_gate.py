from types import SimpleNamespace


def _summary(structured_mean=0.01, null_mean=0.0, null_material=0.0):
    from esdm.validate.v04_r6_matched import V04R6Summary, V04R6WorldSummary

    return V04R6Summary(
        worlds={
            "structured": V04R6WorldSummary(
                world="structured",
                replicates=16,
                positive_gain_rate=1.0,
                material_gain_rate=0.8,
                mean_gain=structured_mean,
                min_gain=-0.001,
                max_gain=0.02,
                total_divergences=0,
            ),
            "resolution_null": V04R6WorldSummary(
                world="resolution_null",
                replicates=16,
                positive_gain_rate=0.5,
                material_gain_rate=null_material,
                mean_gain=null_mean,
                min_gain=-0.01,
                max_gain=0.01,
                total_divergences=0,
            ),
        },
        total_fits=64,
        total_divergences=0,
    )


def test_r6_gate_accepts_structured_advantage_and_null_guard():
    from esdm.validate.v04_r6_gate import evaluate_v04_r6_gate

    decision = evaluate_v04_r6_gate(_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_r6_null_guard_is_required():
    from esdm.validate.v04_r6_gate import evaluate_v04_r6_gate

    assert evaluate_v04_r6_gate(_summary(null_mean=0.006)).passed is False
    assert evaluate_v04_r6_gate(_summary(null_material=0.3125)).passed is False
