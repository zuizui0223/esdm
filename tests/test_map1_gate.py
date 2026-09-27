from esdm.validate.map1_gate import (
    Map1ComparisonSummary,
    Map1GateConfig,
    evaluate_map1_gate,
    summarize_map1_gains,
)
from esdm.validate.map1_known_truth import make_map1_worlds


def _passing_rows():
    positive = set()
    null = set()
    for world in make_map1_worlds():
        for row in world.expected_positive_comparisons:
            positive.add((world.world_id, *row))
        for row in world.expected_null_comparisons:
            null.add((world.world_id, *row))

    rows = []
    for world, candidate, reference, holdout in sorted(positive):
        rows.append(
            Map1ComparisonSummary(
                world, candidate, reference, holdout,
                16, 0.875, 0.75, 0.012,
            )
        )
    for world, candidate, reference, holdout in sorted(null):
        rows.append(
            Map1ComparisonSummary(
                world, candidate, reference, holdout,
                16, 0.5, 0.125, 0.001,
            )
        )
    return rows


def test_map1_gate_passes_only_complete_frozen_pattern():
    decision = evaluate_map1_gate(
        _passing_rows(),
        mean_divergences_per_fit=0.0,
    )
    assert decision.passed
    assert decision.claims["COHERENT_MAP_SUPPORTED"]
    assert all(check.passed for check in decision.checks)


def test_map1_gate_requires_coherence_to_beat_exchangeable_control():
    rows = _passing_rows()
    target = ("P1", "BC", "BX", "H1")
    rows = [
        (
            Map1ComparisonSummary(
                row.world_id,
                row.candidate_model,
                row.reference_model,
                row.holdout,
                row.replicates,
                0.5,
                row.material_gain_rate,
                0.001,
            )
            if row.key == target
            else row
        )
        for row in rows
    ]
    decision = evaluate_map1_gate(
        rows,
        mean_divergences_per_fit=0.0,
    )
    assert not decision.passed
    assert not decision.claims["COHERENT_MAP_SUPPORTED"]


def test_map1_gate_sampling_guardrail_is_independent():
    decision = evaluate_map1_gate(
        _passing_rows(),
        mean_divergences_per_fit=0.11,
    )
    assert not decision.passed
    assert not decision.claims["COHERENT_MAP_SUPPORTED"]


def test_map1_gate_thresholds_are_frozen():
    cfg = Map1GateConfig()
    assert cfg.replicates_per_world == 16
    assert cfg.positive_min_rate == 0.75
    assert cfg.positive_min_mean_gain == 0.005
    assert cfg.null_max_material_rate == 0.25
    assert cfg.null_max_mean_gain == 0.005
    assert cfg.material_gain_threshold == 0.005
    assert cfg.max_mean_divergences_per_fit == 0.10


def test_map1_gain_summary_uses_material_threshold():
    row = summarize_map1_gains(
        "X", "BC", "BX", "H1",
        (-0.01, 0.001, 0.006, 0.02),
    )
    assert row.positive_gain_rate == 0.75
    assert row.material_gain_rate == 0.5
