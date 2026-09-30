from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "replication" / "E4_MICA_POSTRESULT_SYNTHESIS.json"


def _read() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_e4_synthesis_preserves_terminal_empirical_result():
    value = _read()
    frozen = value["frozen_empirical_result"]

    assert value["status"] == "FROZEN_POSTRESULT_SYNTHESIS"
    assert frozen["sampling_gate_passed"] is True
    assert frozen["total_divergences"] == 0
    assert frozen["heldout_deployment_rows"] == 733
    assert frozen["scores"]["activity_gain"] == pytest.approx(
        -0.6390511804117178
    )
    assert frozen["scores"]["state_gain"] == pytest.approx(
        0.008390925023042506
    )


def test_e4_synthesis_activity_is_robust_under_both_block_definitions():
    value = _read()["uncertainty_audits"]

    deployment = value["deployment_blocks"]["activity"]
    location = value["physical_location_blocks"]["activity"]
    assert deployment["category"] == "robust_non_generalizing"
    assert deployment["upper_bound"] < 0.0
    assert location["category"] == "robust_non_generalizing"
    assert location["upper_bound"] < 0.0

    state_d = value["deployment_blocks"]["state"]
    state_l = value["physical_location_blocks"]["state"]
    assert state_d["category"] == "uncertain"
    assert state_d["lower_bound"] < 0.0 < state_d["upper_bound"]
    assert state_l["category"] == "uncertain"
    assert state_l["lower_bound"] < 0.0 < state_l["upper_bound"]


def test_e4_synthesis_records_domain_shift_without_causal_promotion():
    value = _read()

    geometry = value["failure_geometry"]
    assert geometry["deployment_level"]["event_bearing_negative_activity_gain"] == 127
    assert geometry["location_level"]["heldout_unique_locations"] == 27
    assert geometry["location_level"]["all_leave_one_location_out_activity_means_negative"] is True
    assert geometry["source_domain"]["D_prefix_heldout_focal_event_fraction"] > 0.98

    cross = value["diel_domain_shift"]["cross_taxon_negative_control"]
    assert cross["eligible_binomial_species"] == 8
    assert cross["species_with_lower_heldout_D_night_day_ratio"] == 7
    assert cross["nonfocal_species_with_lower_ratio"] == 6
    assert cross["focal_negative_shift_rank_most_negative_is_1"] == 6

    limit = value["identifiability_limit"]
    assert limit["activity_and_effective_detection_separable_in_E4"] is False
    assert limit["causal_behavioral_nonstationarity_identified"] is False
    assert limit["causal_camera_or_annotation_effect_identified"] is False


def test_e4_synthesis_next_programme_requires_independent_data_and_does_not_open_outcome():
    value = _read()
    future = value["next_independent_programme"]
    governance = value["governance"]

    assert future["may_reuse_E2_E4_response_as_primary_test"] is False
    assert "new independent data not used to fit or diagnose E2-E4" in future[
        "required_before_outcome"
    ]
    assert governance["changes_frozen_E4_result"] is False
    assert governance["changes_E4_support_decisions"] is False
    assert governance["authorizes_E4_rerun"] is False
    assert governance["authorizes_E4_retuning"] is False
    assert governance["authorizes_Laplace_or_INLA_within_E4"] is False
    assert governance["authorizes_E5_outcome_opening"] is False
