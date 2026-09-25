from types import SimpleNamespace

from esdm.validate.v07e_gate import evaluate_v07e_gate
from esdm.validate.v07e_run import V07ESummary


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
        static_better_rate=0.9375,
        mean_static_gain=1.0,
        minimum_static_gain=-0.1,
        total_divergences=0,
    )
    values.update(overrides)
    return V07ESummary(**values)


def test_v07e_gate_accepts_reciprocal_static_specificity():
    decision = evaluate_v07e_gate(_qualification(), _summary())
    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07e_gate_is_symmetric_with_v07d_thresholds():
    assert not evaluate_v07e_gate(
        _qualification(),
        _summary(static_better_rate=0.8125),
    ).passed
    assert not evaluate_v07e_gate(
        _qualification(),
        _summary(mean_static_gain=0.49),
    ).passed


def test_v07e_gate_requires_both_candidates_estimable():
    decision = evaluate_v07e_gate(
        _qualification(dynamic_practical_pass=False),
        _summary(),
    )
    assert not decision.passed
