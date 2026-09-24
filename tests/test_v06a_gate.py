from types import SimpleNamespace

from esdm.validate.v06a_fixture import V06A_RECOVERY_TRUTH
from esdm.validate.v06a_run import V06ASummary


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
        mean_biases={target: 0.02 for target in V06A_RECOVERY_TRUTH},
        coverages={target: 0.875 for target in V06A_RECOVERY_TRUTH},
        positive_gain_rate=0.875,
        mean_gain=0.02,
        minimum_gain=-0.01,
        total_divergences=0,
    )
    values.update(overrides)
    return V06ASummary(**values)


def test_v06a_gate_accepts_recovery_transfer_and_refusal():
    from esdm.validate.v06a_gate import evaluate_v06a_gate

    decision = evaluate_v06a_gate(_qualification(), _summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_v06a_gate_requires_joint_only_refusal():
    from esdm.validate.v06a_gate import evaluate_v06a_gate

    q = _qualification()
    q.joint_only_refusal_pass = False
    assert evaluate_v06a_gate(q, _summary()).passed is False
