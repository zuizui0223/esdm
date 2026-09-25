from types import SimpleNamespace

from esdm.validate.v07d_gate import evaluate_v07d_gate
from esdm.validate.v07d_run import V07DSummary


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
    return V07DSummary(**values)


def test_v07d_gate_accepts_equal_dimension_dynamic_advantage():
    decision = evaluate_v07d_gate(_qualification(), _summary())
    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07d_gate_requires_static_practical_identification():
    decision = evaluate_v07d_gate(
        _qualification(static_practical_pass=False),
        _summary(),
    )
    assert not decision.passed


def test_v07d_gate_keeps_v07c_effect_thresholds():
    assert not evaluate_v07d_gate(
        _qualification(),
        _summary(dynamic_better_rate=0.8125),
    ).passed
    assert not evaluate_v07d_gate(
        _qualification(),
        _summary(mean_dynamic_gain=0.49),
    ).passed
