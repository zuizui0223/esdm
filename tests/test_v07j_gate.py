from esdm.validate.v07j_fixture import V07J_WORLD_ORDER, truth_sites
from esdm.validate.v07j_gate import V07JGateConfig, evaluate_v07j_gate
from esdm.validate.v07j_run import V07JSummary, V07JWorldSummary


def _world(world, **overrides):
    values = dict(
        world=world,
        replicates=12,
        fit_count=24,
        selected_lower_worst_sd_rate=0.75,
        mean_worst_sd_ratio=0.90,
        minimum_worst_sd_ratio=0.60,
        maximum_worst_sd_ratio=1.05,
        selected_mean_biases={target: 0.01 for target in truth_sites(world)},
        selected_coverages={target: 0.75 for target in truth_sites(world)},
        positive_heldout_gain_rate=0.50,
        mean_heldout_gain=0.0,
        minimum_heldout_gain=-0.20,
        total_divergences=0,
    )
    values.update(overrides)
    return V07JWorldSummary(**values)


def _summary(**world_overrides):
    worlds = {
        world: _world(world, **world_overrides.get(world, {}))
        for world in V07J_WORLD_ORDER
    }
    return V07JSummary(
        world_summaries=worlds,
        total_replicates=36,
        total_fit_count=72,
        total_divergences=sum(row.total_divergences for row in worlds.values()),
        pooled_mean_worst_sd_ratio=sum(
            row.mean_worst_sd_ratio for row in worlds.values()
        ) / len(worlds),
        pooled_selected_lower_worst_sd_rate=sum(
            row.selected_lower_worst_sd_rate for row in worlds.values()
        ) / len(worlds),
    )


def test_v07j_gate_passes_only_when_every_shift_world_passes():
    decision = evaluate_v07j_gate(_summary())
    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07j_one_failed_shift_world_fails_entire_gate():
    decision = evaluate_v07j_gate(
        _summary(high_turnover={"mean_worst_sd_ratio": 0.951})
    )
    assert not decision.passed
    failed = [
        check for check in decision.checks
        if check.name == "high_turnover:mean_worst_sd_ratio"
    ]
    assert len(failed) == 1
    assert not failed[0].passed


def test_v07j_prediction_is_not_a_gate_criterion():
    decision = evaluate_v07j_gate(
        _summary(
            low_occupancy={
                "positive_heldout_gain_rate": 0.0,
                "mean_heldout_gain": -1.0,
                "minimum_heldout_gain": -2.0,
            }
        )
    )
    assert decision.passed
    assert not any("heldout" in check.name for check in decision.checks)


def test_v07j_gate_freezes_three_world_twelve_replicate_profile():
    config = V07JGateConfig()
    assert config.replicates_per_world == 12
    assert config.min_selected_lower_worst_sd_rate == 0.75
    assert config.max_mean_worst_sd_ratio == 0.95
    assert config.max_abs_mean_bias == 0.20
    assert config.min_coverage == 2.0 / 3.0
    assert config.max_mean_divergences_per_fit == 0.10
