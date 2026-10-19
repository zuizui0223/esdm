"""Synthetic and frozen-receipt guardrails for the exploratory community diel audit."""
from __future__ import annotations

import math
from pathlib import Path

from scripts.audit_e4_community_relative_diel import (
    CONTRACT_STATUS, EXPECTED, MIN_INFORMATIVE_SITES,
    MUSKRAT, RAT, _mh, site_summary,
)

ROOT = Path(__file__).resolve().parents[1]


def test_rodent_observed_rank_reversal_is_a_frozen_aggregate_fact():
    def relative_odds(cohort):
        rat_n, rat_d = EXPECTED[cohort][RAT]
        mus_n, mus_d = EXPECTED[cohort][MUSKRAT]
        return rat_n * mus_d / (rat_d * mus_n)

    train = relative_odds("training")
    east = relative_odds("heldout_D")
    assert math.isclose(train, 0.7591696625466406, rel_tol=1e-12)
    assert math.isclose(east, 7.2867933919875165, rel_tol=1e-12)
    assert math.isclose(east / train, 9.598372737319231, rel_tol=1e-12)
    assert train < 1 < east


def test_common_site_diel_observation_multiplier_cancels_exactly():
    # The ratio is invariant only to a species-common *within-site*
    # observation multiplier. This is not evidence that it is shared in MICA.
    rat_n, rat_d, mus_n, mus_d = 30.0, 5.0, 12.0, 8.0
    before = (rat_n / rat_d) / (mus_n / mus_d)
    for night_factor, day_factor in ((0.1, 3.0), (10.0, 0.05)):
        after = ((rat_n * night_factor) / (rat_d * day_factor)) / (
            (mus_n * night_factor) / (mus_d * day_factor)
        )
        assert math.isclose(before, after, rel_tol=1e-12)


def test_site_stratification_can_differ_from_pooled_composition():
    sites = {
        "A": {"rat_n": 3, "rat_d": 1, "mus_n": 1, "mus_d": 2},
        "B": {"rat_n": 6, "rat_d": 2, "mus_n": 2, "mus_d": 4},
        "C": {"rat_n": 9, "rat_d": 3, "mus_n": 3, "mus_d": 6},
        "rat-only": {"rat_n": 2000, "rat_d": 1, "mus_n": 0, "mus_d": 0},
    }
    out = site_summary(sites)
    assert out["physical_locations"] == 4
    assert out["locations_with_both_species_recorded"] == 3
    assert out["locations_informative_for_site_stratified_diel_contrast"] == 3
    assert out["recorded_rat_events_in_shared_locations"] == 24
    assert out["recorded_muskrat_events_in_shared_locations"] == 18
    assert math.isclose(
        out["site_stratified_mantel_haenszel_rat_over_muskrat_odds"], 6
    )
    assert out["leave_one_informative_location_out"]["valid_contrasts"] == 0


def test_insufficient_shared_sites_refuses_even_with_large_total_counts():
    sites = {
        "a": {"rat_n": 20000, "rat_d": 150, "mus_n": 0, "mus_d": 0},
        "b": {"rat_n": 0, "rat_d": 0, "mus_n": 5000, "mus_d": 1000},
        "c": {"rat_n": 30, "rat_d": 10, "mus_n": 25, "mus_d": 5},
        "d": {"rat_n": 40, "rat_d": 20, "mus_n": 15, "mus_d": 10},
    }
    out = site_summary(sites)
    assert MIN_INFORMATIVE_SITES == 3
    assert out["locations_informative_for_site_stratified_diel_contrast"] == 2
    assert out["site_stratified_mantel_haenszel_rat_over_muskrat_odds"] is None
    assert out["site_stratified_status"] == "INSUFFICIENT_MATCHED_SITE_IDENTIFICATION"


def test_site_stratification_does_not_silently_impute_zero_cells():
    sites = [
        {"rat_n": 100, "rat_d": 0, "mus_n": 200, "mus_d": 0},
        {"rat_n": 5, "rat_d": 2, "mus_n": 1, "mus_d": 0},
        {"rat_n": 2, "rat_d": 3, "mus_n": 3, "mus_d": 4},
    ]
    assert _mh(sites) is None


def test_research_workflow_is_source_pinned_and_non_fitting():
    assert "POSTRESULT" in CONTRACT_STATUS
    workflow = (
        ROOT / ".github" / "workflows"
        / "e4-mica-community-relative-diel-once.yml"
    ).read_text(encoding="utf-8")
    assert "run-id: 36369531079" in workflow
    assert "E2_MICA_TEMPORAL_INTEGRITY_RESULT.json" in workflow
    assert "E4_MICA_POSTRESULT_CROSS_TAXON_DIEL_SUPPLEMENT.json" in workflow
    assert "audit_e4_community_relative_diel.py" in workflow
    assert "upload-artifact" in workflow
    for forbidden in ("fit_e4_mica_sparse", "num_warmup", "num_samples", "workflow_dispatch", "inla", "Laplace"):
        assert forbidden not in workflow
