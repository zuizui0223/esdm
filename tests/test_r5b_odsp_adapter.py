from __future__ import annotations

import pytest

from esdm.transfer import (
    build_v04_r5b_activity_odsp_bundle,
    build_v04_r5b_state_odsp_bundle,
)


def _result():
    rows = []
    for replicate, (activity_knockout, state_knockout, full) in enumerate(
        (
            (-0.61, -0.64, -0.60),
            (-0.59, -0.63, -0.585),
            (-0.62, -0.65, -0.605),
        )
    ):
        rows.append(
            {
                "replicate": replicate,
                "posterior_means": {},
                "posterior_lows": {},
                "posterior_highs": {},
                "full_heldout_log_score": full,
                "activity_knockout_heldout_log_score": activity_knockout,
                "state_knockout_heldout_log_score": state_knockout,
                "full_divergences": 0,
                "activity_knockout_divergences": 0,
                "state_knockout_divergences": 0,
                "activity_gain": full - activity_knockout,
                "state_gain": full - state_knockout,
            }
        )
    return {
        "schema": "esdm.v04_r5b.outcome.v1",
        "status": "PASS",
        "git_sha": "frozen-r5b",
        "infrastructure_block": None,
        "replicates": rows,
    }


def test_r5b_activity_binding_is_a_strict_two_level_information_contrast():
    bundle = build_v04_r5b_activity_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_v04_r5b_activity_transfer_v1"
    assert bundle.contract["levels"] == [
        {
            "name": "suitability_state",
            "information": ["suitability", "state"],
            "score_column": "score__suitability_state",
        },
        {
            "name": "suitability_state_activity",
            "information": ["suitability", "state", "activity"],
            "score_column": "score__suitability_state_activity",
        },
    ]
    assert bundle.rows[0]["score__suitability_state"] == pytest.approx(-0.61)
    assert bundle.rows[0]["score__suitability_state_activity"] == pytest.approx(-0.60)
    assert bundle.manifest["source_schema"] == "esdm.v04_r5b.outcome.v1"


def test_r5b_state_binding_is_a_separate_two_level_information_contrast():
    bundle = build_v04_r5b_state_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_v04_r5b_state_transfer_v1"
    assert bundle.contract["levels"] == [
        {
            "name": "suitability_activity",
            "information": ["suitability", "activity"],
            "score_column": "score__suitability_activity",
        },
        {
            "name": "suitability_activity_state",
            "information": ["suitability", "activity", "state"],
            "score_column": "score__suitability_activity_state",
        },
    ]
    assert bundle.rows[0]["score__suitability_activity"] == pytest.approx(-0.64)
    assert bundle.rows[0]["score__suitability_activity_state"] == pytest.approx(-0.60)


def test_r5b_activity_and_state_are_parallel_not_an_ordered_three_level_ladder():
    activity = build_v04_r5b_activity_odsp_bundle(_result())
    state = build_v04_r5b_state_odsp_bundle(_result())

    activity_levels = activity.contract["levels"]
    state_levels = state.contract["levels"]

    assert activity_levels[-1]["score_column"] != state_levels[-1]["score_column"]
    assert activity.rows[0][activity_levels[-1]["score_column"]] == pytest.approx(
        state.rows[0][state_levels[-1]["score_column"]]
    )
    assert set(activity_levels[0]["information"]) == {"suitability", "state"}
    assert set(state_levels[0]["information"]) == {"suitability", "activity"}
    assert "activity" not in activity_levels[0]["information"]
    assert "state" not in state_levels[0]["information"]


def test_r5b_export_requires_frozen_pass_outcome():
    failed = _result()
    failed["status"] = "FAIL"
    with pytest.raises(ValueError, match="frozen PASS"):
        build_v04_r5b_activity_odsp_bundle(failed)

    blocked = _result()
    blocked["infrastructure_block"] = {"reason": "blocked"}
    with pytest.raises(ValueError, match="infrastructure-blocked"):
        build_v04_r5b_state_odsp_bundle(blocked)


def test_r5b_export_preserves_independent_replicate_semantics():
    activity = build_v04_r5b_activity_odsp_bundle(_result())
    state = build_v04_r5b_state_odsp_bundle(_result())

    assert activity.manifest["group_semantics"] == (
        "independent semi-synthetic known-truth replicate"
    )
    assert state.manifest["group_semantics"] == (
        "independent semi-synthetic known-truth replicate"
    )
    assert activity.contract["evaluation"]["analysis_mode"] == "descriptive"
    assert state.contract["evaluation"]["analysis_mode"] == "descriptive"
