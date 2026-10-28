"""Regression-lock E7 aggregate-only transfer components and claim boundaries."""
from __future__ import annotations

import json
import math
from pathlib import Path

from scripts.e7_pair_transfer_decomposition import analyze
from scripts.e7_relational_coherence import load_pinned_pair_table

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "replication"
RECEIPT = DOC / "E7_PAIR_TRANSFER_COMPONENTS_RESULT_RECEIPT.json"
PAIR = DOC / "E7_RELATIONAL_PAIRWISE_66.csv"


def test_receipt_is_inspectable_and_no_new_wildlife_response_was_opened():
    x = json.loads(RECEIPT.read_text(encoding="utf-8"))
    p = x["provenance"]
    assert p["workflow_run_id"] == 40614625337
    assert p["workflow_conclusion"] == "success"
    assert p["artifact_id"] == 12783798278
    assert p["artifact_zip_sha256"] == "a83f0dbd846c9ef785771013f7c2c025fafb233f16f4298c3a357bc762e162cc"
    assert p["generated_json_sha256"] == "26f4fb6e852c137f86e27f8426ee56d108170f1828ba1c039190e3d83456b1b6"
    assert x["science_boundaries"]["aggregate_only_rederived_no_new_wildlife_event_rows"] is True
    assert x["science_boundaries"]["original_E5_qualified_candidates"] == 0
    assert x["science_boundaries"]["original_E5_G4_passed"] is False


def test_independent_receipt_rounds_to_recomputed_46_edge_decomposition():
    frozen=json.loads(RECEIPT.read_text(encoding="utf-8"))
    computed=analyze(load_pinned_pair_table(PAIR),check_original=True)
    f,c=frozen["discovery_validation"],computed["cross_period"]
    keys={
        "raw_pair_cosine":"raw_pair_vector_cosine",
        "species_gradient_cosine":"gradient_component_cosine",
        "graph_residual_cosine":"residual_component_cosine",
        "raw_cross_dot":"raw_dot",
        "gradient_cross_dot":"gradient_dot",
        "residual_cross_dot":"residual_dot",
        "direct_full_discovery_to_validation_skill_vs_zero":"historical_full_pairs_on_validation_skill_vs_zero",
        "discovery_gradient_to_raw_validation_skill_vs_zero":"historical_gradient_on_validation_skill_vs_zero",
        "discovery_gradient_to_validation_gradient_skill_vs_zero":"historical_gradient_on_validation_gradient_skill_vs_zero",
        "discovery_cycle_to_validation_cycle_skill_vs_zero":"historical_residual_on_validation_residual_skill_vs_zero",
    }
    for old,new in keys.items():
        assert math.isclose(f[old],c[new],rel_tol=1e-12,abs_tol=1e-12)
    assert frozen["support"]["graph_cycle_dimension"] == computed["shared_graph"]["independent_cycle_space_dimension"] == 36
    assert f["leave_one_taxon_out_exclusions"] == c["leave_one_taxon_exclusions"] == 11
    assert f["gradient_positive_residual_negative_exclusions"] == c["positive_gradient_negative_residual_leave_one_taxon_count"] == 10
    s=frozen["noncollapsibility_counterexample"]
    q=computed["stationary_diel_synthetic_counterexample"]
    assert s["same_sites_for_all_three_pairs"] is True
    assert s["each_species_wet_and_dry_night_midday_ratio_identical_at_each_site"] is True
    assert math.isclose(s["triangle_closure_log_units"],q["synthetic_triangle_closure_log_units"],abs_tol=1e-12)


def test_report_does_not_call_nonclosure_an_ecological_interaction():
    txt=(DOC/"E7_PAIR_TRANSFER_COMPONENTS_AND_NONCOLLAPSIBILITY.md").read_text(encoding="utf-8")
    assert "noncollapsibility" in txt.lower()
    assert "not a biological three-way interaction" in txt.lower()
    assert "10 of the 11" in txt
    assert "zero by linear-algebra construction" in txt
