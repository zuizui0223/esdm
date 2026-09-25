from types import SimpleNamespace

from esdm.validate.v07b_fixture import V07B_TRUTH
from esdm.validate.v07b_run import V07BSummary


def _qualification():
    return SimpleNamespace(
        positive_structural_pass=True,
        positive_practical_pass=True,
        joint_only_refusal_pass=True,
    )


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        mean_biases={target: 0.05 for target in V07B_TRUTH},
        coverages={target: 0.875 for target in V07B_TRUTH},
        positive_gain_rate=0.9375,
        mean_gain=1.5,
        minimum_gain=-0.1,
        total_divergences=0,
    )
    values.update(overrides)
    return V07BSummary(**values)


def test_v07b_gate_accepts_recovery_and_late_transfer():
    from esdm.validate.v07b_gate import evaluate_v07b_gate

    decision = evaluate_v07b_gate(_qualification(), _summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_v07b_gate_refuses_weak_late_transfer():
    from esdm.validate.v07b_gate import evaluate_v07b_gate

    assert evaluate_v07b_gate(
        _qualification(),
        _summary(positive_gain_rate=0.75),
    ).passed is False
    assert evaluate_v07b_gate(
        _qualification(),
        _summary(mean_gain=0.1),
    ).passed is False


def test_v07b_gate_requires_identification_qualification():
    from esdm.validate.v07b_gate import evaluate_v07b_gate

    q = _qualification()
    q.positive_practical_pass = False
    assert evaluate_v07b_gate(q, _summary()).passed is False
