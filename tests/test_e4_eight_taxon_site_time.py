"""Synthetic-only correctness tests for eight-taxon post-outcome camera audit."""
from __future__ import annotations

from collections import Counter, defaultdict
import itertools
import math

from scripts.audit_e4_eight_taxon_site_time import (
    COHORTS, MODE_NAMES, TAXA, MIN_SITES, MIN_CELLS, MIN_TIME_BINS,
    cell_rows, estimate_mh, pair_in_cohort, pair_summary, temporal_bin,
)
from datetime import datetime


def _counts(entries):
    out = defaultdict(Counter)
    for site, segment, a, b, c, d in entries:
        out[(site, segment)][("Ondatra zibethicus", "night")] = a
        out[(site, segment)][("Ondatra zibethicus", "day")] = b
        out[(site, segment)][("Rattus norvegicus", "night")] = c
        out[(site, segment)][("Rattus norvegicus", "day")] = d
    return out


def test_fixed_eight_taxa_is_all_28_pairs_without_response_ranking():
    assert tuple(sorted(TAXA)) == TAXA
    assert len(TAXA) == 8
    assert len(set(itertools.combinations(TAXA, 2))) == 28
    assert "Rattus norvegicus" in TAXA
    assert "Ondatra zibethicus" in TAXA


def test_one_camera_season_mh_identity_when_each_cell_identical():
    # Ondatra/Rattus odds = (6/2)/(2/4) = 6, all eight strata.
    cells = _counts([
        (site, season, 6, 2, 2, 4)
        for site in ("s1", "s2", "s3", "s4")
        for season in ("spring", "autumn")
    ])
    rows = cell_rows(cells, "Ondatra zibethicus", "Rattus norvegicus")
    out = estimate_mh(rows)
    assert (MIN_SITES, MIN_CELLS, MIN_TIME_BINS) == (3, 4, 2)
    assert (out["informative_physical_sites"], out["informative_site_time_cells"]) == (4, 8)
    assert out["informative_time_bins"] == 2
    assert out["status"] == "DESCRIPTIVE_ESTIMABLE"
    assert math.isclose(out["odds_ratio"], 6.0)
    summary = pair_in_cohort(cells, "Ondatra zibethicus", "Rattus norvegicus")
    assert summary["leave_one_physical_site_out"]["calculable"] == 4
    assert math.isclose(summary["leave_one_physical_site_out"]["minimum"], 6.0)
    assert math.isclose(summary["leave_one_physical_site_out"]["maximum"], 6.0)


def test_one_shared_site_cannot_make_transfer_comparable_despite_huge_events():
    cells = _counts([
        ("s1", "winter", 3000, 100, 5000, 100),
        ("s1", "spring", 3000, 100, 5000, 100),
        ("s1", "summer", 3000, 100, 5000, 100),
        ("s1", "autumn", 3000, 100, 5000, 100),
    ])
    r = pair_in_cohort(cells, "Ondatra zibethicus", "Rattus norvegicus")
    assert r["status"] == "INSUFFICIENT_SITE_TIME_SUPPORT"
    assert r["odds_ratio"] is None
    assert r["informative_physical_sites"] == 1


def test_time_cooccurrence_required_not_merely_same_physical_location():
    cells = _counts([
        ("s1", "winter", 100, 40, 0, 0),
        ("s1", "spring", 0, 0, 100, 40),
        ("s2", "winter", 100, 40, 0, 0),
        ("s2", "spring", 0, 0, 100, 40),
    ])
    out = pair_in_cohort(cells, "Ondatra zibethicus", "Rattus norvegicus")
    assert out["informative_site_time_cells"] == 0
    assert out["status"] == "INSUFFICIENT_SITE_TIME_SUPPORT"


def test_zero_product_uses_explicit_nonestimable_not_pseudocount():
    rows = [
        (site, season, 4, 0, 0, 4)
        for site in ("a", "b", "c", "d")
        for season in ("spring", "autumn")
    ]
    out = estimate_mh(rows)
    assert out["status"] == "ZERO_MH_CROSSPRODUCT"
    assert out["odds_ratio"] is None


def test_all_pair_results_include_refusals_not_selected_after_estimation():
    cells = {
        "training": _counts([
            (site, season, 6, 2, 2, 4)
            for site in ("a", "b", "c", "d")
            for season in ("spring", "autumn")
        ]),
        "heldout_D": _counts([
            (site, season, 2, 4, 6, 2)
            for site in ("u", "v", "w", "x")
            for season in ("spring", "autumn")
        ]),
    }
    out = pair_summary(cells)
    assert out["fixed_pair_universe"] == 28
    assert len(out["all_28_pairs_in_fixed_taxonomic_order"]) == 28
    assert out["comparable_pairs"] == 1
    assert out["pairs_with_observed_rank_reversal"] == 1
    assert out["reversals_stable_under_all_computable_leave_one_site_out"] == 1
    rodent = out["rodent_rat_over_muskrat"]
    assert rodent["rank_reversal"] is True
    assert rodent["reversal_survives_site_deletions"] is True
    assert math.isclose(rodent["training_odds"], 1/6)
    assert math.isclose(rodent["heldout_D_odds"], 6)


def test_season_and_year_month_binning_without_using_detection_outcomes():
    jan, jul = datetime(2025, 1, 16), datetime(2025, 7, 16)
    assert temporal_bin(jan, "site_season") == "winter"
    assert temporal_bin(jul, "site_season") == "summer"
    assert temporal_bin(jan, "site_yearmonth") == "2025-01"
    assert temporal_bin(jul, "site_yearmonth") == "2025-07"
    assert MODE_NAMES == ("site_season", "site_yearmonth")
    assert COHORTS == ("training", "heldout_D")
