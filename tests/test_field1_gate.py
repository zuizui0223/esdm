from esdm.validate.field1_gate import (
    Field1ComparisonSummary,
    Field1GateConfig,
    evaluate_field1_gate,
    summarize_field1_gains,
)
from esdm.validate.field1_known_truth import (
    make_field1_mean_covariance_factorial,
    make_field1_primary_worlds,
)


def _passing_rows():
    rows = []
    positive = set()
    null = set()
    for world in (
        *make_field1_primary_worlds(),
        *make_field1_mean_covariance_factorial(),
    ):
        for candidate, reference, holdout in world.expected_positive_comparisons:
            positive.add((world.world_id, candidate, reference, holdout))
        for candidate, reference, holdout in world.expected_null_comparisons:
            null.add((world.world_id, candidate, reference, holdout))

    for world, candidate, reference, holdout in sorted(positive):
        rows.append(
            Field1ComparisonSummary(
                world,
                candidate,
                reference,
                holdout,
                replicates=16,
                positive_gain_rate=0.875,
                material_gain_rate=0.75,
                mean_gain=0.012,
            )
        )
    for world, candidate, reference, holdout in sorted(null):
        rows.append(
            Field1ComparisonSummary(
                world,
                candidate,
                reference,
                holdout,
                replicates=16,
                positive_gain_rate=0.5,
                material_gain_rate=0.125,
                mean_gain=0.001,
            )
        )
    return rows


def test_field1_gate_passes_only_when_all_frozen_checks_pass():
    decision = evaluate_field1_gate(
        _passing_rows(),
        k6_distance_match_passed=True,
        mean_divergences_per_fit=0.0,
    )
    assert decision.passed
    assert all(decision.claims.values())
    assert all(check.passed for check in decision.checks)


def test_field1_gate_keeps_axis_claims_separate():
    rows = _passing_rows()
    target = ("K2", "M2", "M1", "H1")
    rows = [
        (
            Field1ComparisonSummary(
                row.world_id,
                row.candidate_model,
                row.reference_model,
                row.holdout,
                row.replicates,
                positive_gain_rate=0.5,
                material_gain_rate=row.material_gain_rate,
                mean_gain=0.001,
            )
            if row.key == target
            else row
        )
        for row in rows
    ]

    decision = evaluate_field1_gate(
        rows,
        k6_distance_match_passed=True,
        mean_divergences_per_fit=0.0,
    )

    assert not decision.passed
    assert decision.claims["FIELD_PRESENT"]
    assert not decision.claims["ENV_DEPENDENCE_SUPPORTED"]
    assert decision.claims["BARRIER_DEPENDENCE_SUPPORTED"]
    assert not decision.claims["FULL_MAP_STRUCTURE_SUPPORTED"]


def test_field1_gate_requires_k6_before_barrier_claim():
    decision = evaluate_field1_gate(
        _passing_rows(),
        k6_distance_match_passed=False,
        mean_divergences_per_fit=0.0,
    )

    assert not decision.passed
    assert not decision.claims["BARRIER_DEPENDENCE_SUPPORTED"]
    assert not decision.claims["FULL_MAP_STRUCTURE_SUPPORTED"]


def test_field1_gate_rejects_missing_or_extra_comparisons():
    rows = _passing_rows()

    try:
        evaluate_field1_gate(
            rows[:-1],
            k6_distance_match_passed=True,
            mean_divergences_per_fit=0.0,
        )
    except ValueError as exc:
        assert "missing comparisons" in str(exc)
    else:
        raise AssertionError("missing comparison must fail closed")

    extra = Field1ComparisonSummary(
        "K999",
        "M4",
        "M0",
        "H1",
        16,
        1.0,
        1.0,
        1.0,
    )
    try:
        evaluate_field1_gate(
            [*rows, extra],
            k6_distance_match_passed=True,
            mean_divergences_per_fit=0.0,
        )
    except ValueError as exc:
        assert "undeclared comparisons" in str(exc)
    else:
        raise AssertionError("undeclared comparison must fail closed")


def test_field1_gate_thresholds_are_frozen_to_preoutcome_values():
    cfg = Field1GateConfig()
    assert cfg.replicates_per_world == 16
    assert cfg.positive_min_rate == 0.75
    assert cfg.positive_min_mean_gain == 0.005
    assert cfg.null_max_material_rate == 0.25
    assert cfg.null_max_mean_gain == 0.005
    assert cfg.material_gain_threshold == 0.005
    assert cfg.max_mean_divergences_per_fit == 0.10



def test_field1_gain_summary_uses_frozen_material_threshold():
    row = summarize_field1_gains(
        "Kx",
        "M2",
        "M1",
        "H1",
        (-0.01, 0.001, 0.006, 0.02),
    )
    assert row.replicates == 4
    assert row.positive_gain_rate == 0.75
    assert row.material_gain_rate == 0.5
    assert row.mean_gain == (-0.01 + 0.001 + 0.006 + 0.02) / 4
