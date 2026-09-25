from __future__ import annotations

import json
from pathlib import Path

import pytest

from esdm.transfer import (
    build_transfer_evidence_portfolio,
    load_transfer_source_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ODSP_TRANSFER_SOURCE_REGISTRY_V1.json"


def _portfolio():
    sources = load_transfer_source_registry(REGISTRY)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return build_transfer_evidence_portfolio(
        repository_root=ROOT,
        registry_id=registry["registry_id"],
        sources=sources,
    )


def test_portfolio_contains_only_validated_exportable_sources():
    portfolio = _portfolio()
    ids = [item.source_id for item in portfolio.items]

    assert ids == [
        "v04_r5b_activity",
        "v04_r5b_state",
        "v06a_static_accessibility",
        "v07b_dynamic_occupancy",
    ]


def test_portfolio_normalizes_frozen_population_results_without_ranking():
    portfolio = _portfolio()
    items = {item.source_id: item for item in portfolio.items}

    activity = items["v04_r5b_activity"]
    state = items["v04_r5b_state"]
    accessibility = items["v06a_static_accessibility"]
    dynamics = items["v07b_dynamic_occupancy"]

    assert activity.population_mean_gain == pytest.approx(0.00699856015906225)
    assert activity.mean_interval_lower == pytest.approx(0.00539876274739076)
    assert activity.conservative_mean_value == pytest.approx(0.00539876274739076)
    assert activity.prediction_lower > 0

    assert state.population_mean_gain == pytest.approx(0.02896466849576273)
    assert state.conservative_mean_value == pytest.approx(0.025782042061382092)

    assert accessibility.population_mean_gain == pytest.approx(0.36244191577864204)
    assert accessibility.conservative_mean_value == pytest.approx(0.27041044003054493)
    assert accessibility.prediction_lower < 0 < accessibility.prediction_upper

    assert dynamics.population_mean_gain == pytest.approx(7.090827989764035)
    assert dynamics.conservative_mean_value == pytest.approx(6.112566461456692)
    assert dynamics.prediction_lower > 0

    assert all(item.population_status == "positive" for item in portfolio.items)


def test_activity_and_state_are_parallel_siblings_not_an_ordered_chain():
    portfolio = _portfolio()
    items = {item.source_id: item for item in portfolio.items}

    assert items["v04_r5b_activity"].parallel_family == "v04_r5b_activity_state"
    assert items["v04_r5b_state"].parallel_family == "v04_r5b_activity_state"
    assert items["v04_r5b_activity"].ordering_relation == "parallel_nonordered"
    assert items["v04_r5b_state"].ordering_relation == "parallel_nonordered"

    assert portfolio.parallel_families == (
        {
            "family": "v04_r5b_activity_state",
            "members": ["v04_r5b_activity", "v04_r5b_state"],
            "shared_programme": True,
            "shared_score_currency": True,
            "natural_order_authorized": False,
            "combined_chain_authorized": False,
            "additive_total_authorized": False,
            "magnitude_ranking_authorized": False,
        },
    )


def test_matching_score_units_do_not_authorize_cross_programme_ranking():
    payload = _portfolio().as_dict()
    boundary = payload["comparison_boundary"]

    assert boundary["cross_programme_numeric_ranking_authorized"] is False
    assert boundary["same_score_unit_implies_comparability"] is False
    assert boundary["parallel_sibling_ordering_authorized"] is False
    assert boundary["parallel_sibling_addition_authorized"] is False
    assert boundary["single_global_information_ladder_authorized"] is False
    assert boundary["lattice_inference_created"] is False

    items = {row["source_id"]: row for row in payload["items"]}
    assert items["v06a_static_accessibility"]["score_unit"] == (
        items["v07b_dynamic_occupancy"]["score_unit"]
    )
    assert items["v06a_static_accessibility"]["programme"] != (
        items["v07b_dynamic_occupancy"]["programme"]
    )


def test_portfolio_never_authorizes_eog_or_n4_action():
    payload = _portfolio().as_dict()
    boundary = payload["action_boundary"]

    assert boundary["authorizes_state_promotion"] is False
    assert boundary["authorizes_eog_consumption"] is False
    assert boundary["authorizes_spatial_patch_ranking"] is False
    assert boundary["authorizes_survey_site_selection"] is False
    assert boundary["authorizes_n4_action"] is False
    assert boundary["n4_survey_action_owner"] == "ACSP"


def test_portfolio_fingerprint_is_deterministic():
    first = _portfolio()
    second = _portfolio()

    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64
