from esdm.validate.amap1_gate import (
    AMap1GateConfig,
    AMap1WorldSummary,
    evaluate_amap1_gate,
    summarize_amap1_world,
)
from esdm.validate.amap1_known_truth import make_amap1_worlds


def _passing_summaries():
    rows = []
    for world in make_amap1_worlds():
        if world.detectability_reference is None:
            rows.append(
                AMap1WorldSummary(
                    world_id=world.world_id,
                    geometry_id=world.geometry_id,
                    truth_id=world.truth_id,
                    oracle_model_id=world.oracle_model_id,
                    replicates=16,
                    material_regret_rate=0.125,
                    mean_regret=0.001,
                    detectability_positive_rate=None,
                    detectability_mean_gain=None,
                )
            )
        else:
            rows.append(
                AMap1WorldSummary(
                    world_id=world.world_id,
                    geometry_id=world.geometry_id,
                    truth_id=world.truth_id,
                    oracle_model_id=world.oracle_model_id,
                    replicates=16,
                    material_regret_rate=0.125,
                    mean_regret=0.001,
                    detectability_positive_rate=0.875,
                    detectability_mean_gain=0.02,
                )
            )
    return rows


def test_amap1_gate_passes_only_when_every_world_and_sampling_pass():
    decision = evaluate_amap1_gate(
        _passing_summaries(),
        mean_divergences_per_fit=0.05,
    )
    assert decision.passed
    assert decision.claims["LOW_REGRET_MAP_SUPPORTED"]
    assert all(check.passed for check in decision.checks)


def test_amap1_gate_does_not_allow_one_geometry_to_rescue_another():
    rows = _passing_summaries()
    target = "G2_TC"
    rows = [
        (
            AMap1WorldSummary(
                world_id=row.world_id,
                geometry_id=row.geometry_id,
                truth_id=row.truth_id,
                oracle_model_id=row.oracle_model_id,
                replicates=row.replicates,
                material_regret_rate=0.375,
                mean_regret=0.02,
                detectability_positive_rate=row.detectability_positive_rate,
                detectability_mean_gain=row.detectability_mean_gain,
            )
            if row.world_id == target
            else row
        )
        for row in rows
    ]

    decision = evaluate_amap1_gate(
        rows,
        mean_divergences_per_fit=0.0,
    )
    assert not decision.passed
    assert not decision.claims["LOW_REGRET_MAP_SUPPORTED"]
    failed_names = {check.name for check in decision.checks if not check.passed}
    assert f"{target}:material_regret_rate" in failed_names
    assert f"{target}:mean_regret" in failed_names


def test_amap1_gate_requires_detectability_in_field_positive_worlds():
    rows = _passing_summaries()
    target = "G3_TX"
    rows = [
        (
            AMap1WorldSummary(
                world_id=row.world_id,
                geometry_id=row.geometry_id,
                truth_id=row.truth_id,
                oracle_model_id=row.oracle_model_id,
                replicates=row.replicates,
                material_regret_rate=row.material_regret_rate,
                mean_regret=row.mean_regret,
                detectability_positive_rate=0.5,
                detectability_mean_gain=0.001,
            )
            if row.world_id == target
            else row
        )
        for row in rows
    ]

    decision = evaluate_amap1_gate(
        rows,
        mean_divergences_per_fit=0.0,
    )
    assert not decision.passed
    failed_names = {check.name for check in decision.checks if not check.passed}
    assert f"{target}:oracle_detectability_rate" in failed_names
    assert f"{target}:oracle_detectability_mean_gain" in failed_names


def test_amap1_gate_requires_sampling_guardrail():
    decision = evaluate_amap1_gate(
        _passing_summaries(),
        mean_divergences_per_fit=0.11,
    )
    assert not decision.passed
    assert not decision.claims["LOW_REGRET_MAP_SUPPORTED"]


def test_amap1_gate_fails_closed_on_missing_or_extra_worlds():
    rows = _passing_summaries()

    try:
        evaluate_amap1_gate(
            rows[:-1],
            mean_divergences_per_fit=0.0,
        )
    except ValueError as exc:
        assert "missing worlds" in str(exc)
    else:
        raise AssertionError("missing AMAP1 world must fail closed")

    extra = AMap1WorldSummary(
        world_id="G9_T9",
        geometry_id="G1",
        truth_id="T0",
        oracle_model_id="B0",
        replicates=16,
        material_regret_rate=0.0,
        mean_regret=0.0,
    )
    try:
        evaluate_amap1_gate(
            [*rows, extra],
            mean_divergences_per_fit=0.0,
        )
    except ValueError as exc:
        assert "undeclared worlds" in str(exc)
    else:
        raise AssertionError("extra AMAP1 world must fail closed")


def test_amap1_gate_thresholds_are_frozen():
    cfg = AMap1GateConfig()
    assert cfg.replicates_per_world == 16
    assert cfg.materiality == 0.005
    assert cfg.positive_min_rate == 0.75
    assert cfg.positive_min_mean_gain == 0.005
    assert cfg.low_regret_max_material_rate == 0.25
    assert cfg.low_regret_max_mean_regret == 0.005
    assert cfg.max_mean_divergences_per_fit == 0.10


def test_amap1_summary_counts_harm_not_beneficial_deviation():
    row = summarize_amap1_world(
        "G1_T0",
        regrets=(-0.02, -0.01, 0.001, 0.006),
    )
    assert row.replicates == 4
    assert row.material_regret_rate == 0.25
    assert row.mean_regret == (-0.02 - 0.01 + 0.001 + 0.006) / 4
    assert row.detectability_positive_rate is None
    assert row.detectability_mean_gain is None


def test_amap1_summary_requires_detectability_for_positive_truth():
    try:
        summarize_amap1_world(
            "G1_TX",
            regrets=(0.0, 0.0),
            detectability_gains=None,
        )
    except ValueError as exc:
        assert "requires detectability gains" in str(exc)
    else:
        raise AssertionError("TX summary without detectability must fail")
