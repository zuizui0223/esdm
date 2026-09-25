from types import SimpleNamespace

from esdm.validate.v07f_gate import evaluate_v07f_gate
from esdm.validate.v07f_run import V07FSummary, V07FWorldSummary


def _qualification(**overrides):
    values = dict(
        dynamic_structural_pass=True,
        dynamic_practical_pass=True,
        static_structural_pass=True,
        static_practical_pass=True,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _world(world, **overrides):
    values = dict(
        world=world,
        replicates=16,
        fit_count=32,
        correct_better_rate=0.8125,
        mean_correct_gain=0.50,
        minimum_correct_gain=-0.1,
        total_divergences=0,
    )
    values.update(overrides)
    return V07FWorldSummary(**values)


def _summary(**world_overrides):
    worlds = {
        "dynamic_like": _world(
            "dynamic_like",
            **world_overrides.get("dynamic_like", {}),
        ),
        "static_like": _world(
            "static_like",
            **world_overrides.get("static_like", {}),
        ),
    }
    return V07FSummary(
        worlds=worlds,
        replicates=32,
        fit_count=64,
        total_divergences=0,
    )


def test_v07f_gate_accepts_bidirectional_misspecified_resolution_signal():
    decision = evaluate_v07f_gate(_qualification(), _summary())
    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07f_gate_requires_each_world_to_discriminate():
    bad = _summary(
        dynamic_like={
            "correct_better_rate": 0.6875,
        }
    )
    assert not evaluate_v07f_gate(_qualification(), bad).passed


def test_v07f_gate_requires_positive_mean_gain_in_each_world():
    bad = _summary(
        static_like={
            "mean_correct_gain": 0.20,
        }
    )
    assert not evaluate_v07f_gate(_qualification(), bad).passed
