from __future__ import annotations

import json
from pathlib import Path

import pytest

import esdm.transfer as transfer
from esdm.transfer import (
    exportable_transfer_sources,
    load_transfer_source_registry,
    require_exportable_transfer_source,
    transfer_source_by_id,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ODSP_TRANSFER_SOURCE_REGISTRY_V1.json"


def _sources():
    return load_transfer_source_registry(REGISTRY)


def test_registry_has_exact_current_exportable_sources():
    sources = _sources()
    exportable = exportable_transfer_sources(sources)

    assert {source.source_id for source in exportable} == {
        "v04_r5b_activity",
        "v04_r5b_state",
        "v06a_static_accessibility",
        "v07b_dynamic_occupancy",
    }
    assert all(source.status == "validated_exportable" for source in exportable)


def test_every_exportable_source_has_live_adapter_and_frozen_receipts():
    for source in exportable_transfer_sources(_sources()):
        assert source.adapter_function is not None
        assert callable(getattr(transfer, source.adapter_function))
        assert source.validated_integration_receipt is not None
        assert (ROOT / source.frozen_receipt).is_file()
        assert (ROOT / source.validated_integration_receipt).is_file()
        assert source.source_artifact_id is not None
        assert source.absolute_score_fields
        assert source.information_levels
        assert source.score_currency is not None


def test_nonexportable_sources_fail_closed_through_registry_api():
    sources = _sources()
    expected = {
        "v05a_directed_interaction": "gain_only_not_exportable",
        "v05b_hidden_common_driver": "scientific_fail_not_exportable",
        "v05e_interaction_evidence_separation": "evidence_tier_not_transfer",
        "v06b_joint_accessibility_identification": "identification_only_not_transfer",
        "v06c_budget_matched_accessibility": "non_nested_comparison_not_transfer",
        "v07a_dynamic_occupancy_identification": "identification_only_not_transfer",
    }

    for source_id, status in expected.items():
        source = transfer_source_by_id(sources, source_id)
        assert source.status == status
        assert source.exportable is False
        assert source.adapter_function is None
        assert source.endpoint_id is None
        assert source.absolute_score_fields == ()
        with pytest.raises(ValueError, match="not ODSP-exportable"):
            require_exportable_transfer_source(sources, source_id)


def test_v05a_gain_only_result_cannot_be_reconstructed_as_absolute_scores():
    source = transfer_source_by_id(_sources(), "v05a_directed_interaction")

    assert source.frozen_result_status == "PASS"
    assert "gain-only" in source.status
    assert "not the two absolute held-out log scores" in source.reason
    assert source.absolute_score_fields == ()
    assert source.score_currency is None


def test_v05b_failure_remains_a_failure_even_with_large_predictive_gain():
    source = transfer_source_by_id(_sources(), "v05b_hidden_common_driver")
    frozen = json.loads((ROOT / source.frozen_receipt).read_text(encoding="utf-8"))

    assert source.status == "scientific_fail_not_exportable"
    assert frozen["status"] == "FAIL"
    assert frozen["summary"]["heldout_positive_gain_rate"] == 1.0
    assert frozen["summary"]["mean_heldout_gain"] > 0
    assert source.exportable is False


def test_v06c_direct_vs_matched_is_not_a_nested_information_filtration():
    source = transfer_source_by_id(_sources(), "v06c_budget_matched_accessibility")

    assert source.status == "non_nested_comparison_not_transfer"
    assert "same ecological information target" in source.reason
    assert source.information_levels == ()


def test_r5b_parallel_family_explicitly_refuses_order():
    sources = _sources()
    activity = transfer_source_by_id(sources, "v04_r5b_activity")
    state = transfer_source_by_id(sources, "v04_r5b_state")

    assert activity.parallel_family == "v04_r5b_activity_state"
    assert state.parallel_family == "v04_r5b_activity_state"
    assert activity.natural_order_with_parallel_sibling is False
    assert state.natural_order_with_parallel_sibling is False

    activity_lower = set(activity.information_levels[0]["information"])
    state_lower = set(state.information_levels[0]["information"])
    assert activity_lower == {"suitability", "state"}
    assert state_lower == {"suitability", "activity"}


def test_exportable_sources_use_strict_nested_information_sets():
    for source in exportable_transfer_sources(_sources()):
        levels = source.information_levels
        assert len(levels) == 2
        assert set(levels[0]["information"]) < set(levels[1]["information"])
        assert {
            level["score_field"] for level in levels
        } == set(source.absolute_score_fields)


def test_registry_boundary_cannot_authorize_new_science_or_action():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    boundary = payload["boundary"]

    assert boundary["registry_authorizes_new_scientific_result"] is False
    assert boundary["registry_authorizes_rerun"] is False
    assert boundary["registry_authorizes_score_reconstruction"] is False
    assert boundary["registry_authorizes_new_information_order"] is False
    assert boundary["registry_authorizes_eog_consumption"] is False
    assert boundary["registry_authorizes_n4_action"] is False


def test_unknown_source_id_fails_closed():
    with pytest.raises(KeyError, match="unknown transfer source"):
        transfer_source_by_id(_sources(), "not-a-source")
