from types import SimpleNamespace

from esdm.validate.v07c_gate import evaluate_v07c_gate
from esdm.validate.v07c_run import V07CSummary


def _qualification(**overrides):
    values = dict(
        dynamic_structural_pass=True,
        dynamic_practical_pass=True,
        static_structural_pass=True,
        static_practical_pass=True,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        dynamic_better_rate=0.9375,
        mean_dynamic_gain=1.0,
        minimum_dynamic_gain=-0.1,
        total_divergences=0,
    )
    values.update(overrides)
    return V07CSummary(**values)


def test_v07c_gate_accepts_matched_dynamic_advantage():
    decision = evaluate_v07c_gate(_qualification(), _summary())
    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07c_gate_requires_static_model_to_be_practically_estimable():
    decision = evaluate_v07c_gate(
        _qualification(static_practical_pass=False),
        _summary(),
    )
    assert not decision.passed


def test_v07c_gate_requires_replicated_late_time_gain():
    decision = evaluate_v07c_gate(
        _qualification(),
        _summary(dynamic_better_rate=0.75),
    )
    assert not decision.passed
