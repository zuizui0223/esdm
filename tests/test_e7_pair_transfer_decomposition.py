"""Synthetic counterexample and 46-pair frozen E7 aggregate regression checks.

No raw LILA wildlife records, camera IDs or new biological event data.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from scripts.e7_pair_transfer_decomposition import (
    analyze, cosine, dot, noncollapsibility_counterexample, skill,
)
from scripts.e7_relational_coherence import load_pinned_pair_table

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "docs" / "replication" / "E7_RELATIONAL_PAIRWISE_66.csv"


def test_no_within_site_diel_change_still_yields_large_mh_triangle_gap():
    x = noncollapsibility_counterexample()
    assert x["identical_three_site_support_for_all_pairs"] is True
    assert x["all_species_have_identical_wet_dry_night_midday_odds_within_each_site"] is True
    assert x["seasonal_multipliers_scale_both_hours_equally_for_each_species"] is True
    assert math.isclose(x["synthetic_triangle_closure_log_units"],1.6050724998448367)
    assert abs(x["synthetic_triangle_closure_log_units"]) > 1


def test_algebraic_helper_rejects_undefined_and_mismatched_vectors():
    assert dot([2,-1],[3,4]) == 2
    assert math.isclose(cosine([3,0],[6,0]),1)
    assert math.isclose(skill([2,2],[0,0]),0)
    with pytest.raises(ValueError):
        dot([1,2],[1])
    with pytest.raises(ValueError):
        cosine([1,0],[0,0])


def test_original_46_pair_cross_period_decomposition_reconciles_exactly():
    r=analyze(load_pinned_pair_table(CSV),check_original=True)
    g=r["shared_graph"]
    c=r["cross_period"]
    assert (g["pair_edges"],g["connected_taxa"],g["independent_cycle_space_dimension"]) == (46,11,36)
    assert g["previous_triangles_are_dependent"] == 104
    assert math.isclose(c["raw_pair_vector_cosine"],0.029631361851061182,abs_tol=1e-12)
    assert math.isclose(c["gradient_component_cosine"],0.42626821279724486,abs_tol=1e-12)
    assert math.isclose(c["residual_component_cosine"],-0.3095896906762198,abs_tol=1e-12)
    assert math.isclose(c["raw_dot"],1.2707981978143295,abs_tol=1e-11)
    assert math.isclose(c["gradient_dot"],8.30559089885213,abs_tol=1e-11)
    assert math.isclose(c["residual_dot"],-7.034792701037792,abs_tol=1e-11)
    assert math.isclose(c["raw_dot"],c["gradient_dot"]+c["residual_dot"],abs_tol=1e-11)
    assert math.isclose(c["historical_gradient_on_validation_skill_vs_zero"],-0.7552148994346888)
    assert math.isclose(c["historical_full_pairs_on_validation_skill_vs_zero"],-2.38229498004733)
    assert c["positive_gradient_negative_residual_leave_one_taxon_count"] == 10
    assert c["leave_one_taxon_exclusions"] == 11
    assert [x["excluded_taxon"] for x in c["leave_one_taxon_sensitivity"]
            if not x["positive_gradient_negative_residual"]] == ["hyenaSpotted"]
    assert r["source"]["new_biological_records_read"] is False
    assert r["interpretation_boundary"]["nonzero_cycle_proves_biological_interactions"] is False
    assert r["interpretation_boundary"]["no_p_values_or_CIs"] is True


def test_only_aggregate_table_is_read_no_biological_workflow_invoked():
    source=(ROOT/"scripts"/"e7_pair_transfer_decomposition.py").read_text(encoding="utf-8")
    assert "load_pinned_pair_table" in source
    assert "E7_RELATIONAL_PAIRWISE_66.csv" not in source or "original_46" in source or "original" in source
    assert "download" not in source
    assert "urlopen" not in source
    assert "ijson" not in source
