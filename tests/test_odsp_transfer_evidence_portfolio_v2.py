from __future__ import annotations

import json
from pathlib import Path

import pytest

from esdm.transfer import (
    PORTFOLIO_SCHEMA_V2,
    build_transfer_evidence_portfolio_v2,
    load_transfer_source_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ODSP_TRANSFER_SOURCE_REGISTRY_V1.json"


def _portfolio():
    sources = load_transfer_source_registry(REGISTRY)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return build_transfer_evidence_portfolio_v2(
        repository_root=ROOT,
        registry_id=registry["registry_id"],
        sources=sources,
    )


def test_v2_ledger_accounts_for_every_registry_source():
    portfolio = _portfolio()
    summary = portfolio.coverage_summary

    assert portfolio.schema == PORTFOLIO_SCHEMA_V2
    assert summary["registry_source_count"] == 14
    assert summary["validated_item_count"] == 4
    assert summary["excluded_source_count"] == 10
    assert summary["scientific_fail_count"] == 2
    assert summary["every_registry_source_accounted_for"] is True
    assert len(portfolio.validated_items) + len(portfolio.excluded_sources) == 14


def test_v2_validated_items_are_exactly_the_existing_four():
    ids = [item.source_id for item in _portfolio().validated_items]

    assert ids == [
        "v04_r5b_activity",
        "v04_r5b_state",
        "v06a_static_accessibility",
        "v07b_dynamic_occupancy",
    ]


def test_v05f_interaction_fail_is_visible_but_not_converted_to_zero():
    excluded = {
        item.source_id: item
        for item in _portfolio().excluded_sources
    }
    row = excluded["v05f_directed_interaction_replication"]

    assert row.registry_status == "scientific_fail_not_exportable"
    assert row.frozen_result_status == "FAIL"
    assert row.exclusion_class == "scientific_gate_failed"
    assert row.numeric_transfer_value_authorized is False
    assert row.unsupported_not_zero is True

    diagnostic = row.diagnostic_summary
    assert diagnostic is not None
    assert diagnostic["positive_world"]["positive_gain_rate"] == 1.0
    assert diagnostic["positive_world"]["mean_heldout_gain"] == pytest.approx(
        1.1190587549523654
    )
    assert diagnostic["specificity_null"]["material_gain_count"] == 5
    assert diagnostic["specificity_null"]["maximum_allowed_count"] == 4
    assert diagnostic["specificity_null"]["material_gain_threshold"] == pytest.approx(
        0.005
    )
    assert diagnostic["specificity_null"]["mean_heldout_gain"] < 0
    assert diagnostic["failed_check"] == "null_material_gain_rate"

    serialized = row.as_dict()
    assert serialized["numeric_transfer_value"] is None
    assert serialized["unsupported_not_zero"] is True


def test_v2_exclusion_classes_distinguish_why_numeric_transfer_is_unavailable():
    excluded = {
        item.source_id: item
        for item in _portfolio().excluded_sources
    }

    assert excluded["v05a_directed_interaction"].exclusion_class == (
        "serialization_ineligible"
    )
    assert excluded["v05b_hidden_common_driver"].exclusion_class == (
        "scientific_gate_failed"
    )
    assert excluded["v05e_interaction_evidence_separation"].exclusion_class == (
        "different_evidence_estimand"
    )
    assert excluded["v06b_joint_accessibility_identification"].exclusion_class == (
        "identification_only"
    )
    assert excluded["v06c_budget_matched_accessibility"].exclusion_class == (
        "non_nested_information"
    )
    assert excluded["v07c_static_vs_dynamic_occupancy"].exclusion_class == (
        "non_nested_information"
    )


def test_v2_selection_boundary_forbids_success_only_reporting():
    payload = _portfolio().as_dict()
    boundary = payload["selection_boundary"]

    assert boundary["excluded_sources_may_be_omitted_from_display"] is False
    assert boundary["unsupported_source_equals_zero_transfer"] is False
    assert boundary["scientific_fail_may_be_promoted_as_numeric_value"] is False
    assert boundary["gain_only_source_may_be_reconstructed"] is False
    assert boundary["non_nested_comparison_may_be_relabelled_as_transfer"] is False


def test_v2_retains_nonranking_and_nonaction_boundaries():
    payload = _portfolio().as_dict()

    comparison = payload["comparison_boundary"]
    action = payload["action_boundary"]

    assert comparison["cross_programme_numeric_ranking_authorized"] is False
    assert comparison["same_score_unit_implies_comparability"] is False
    assert comparison["single_global_information_ladder_authorized"] is False
    assert comparison["lattice_inference_created"] is False

    assert action["authorizes_eog_consumption"] is False
    assert action["authorizes_spatial_patch_ranking"] is False
    assert action["authorizes_survey_site_selection"] is False
    assert action["authorizes_n4_action"] is False
    assert action["n4_survey_action_owner"] == "ACSP"


def test_v2_fingerprint_is_deterministic():
    first = _portfolio()
    second = _portfolio()

    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64
