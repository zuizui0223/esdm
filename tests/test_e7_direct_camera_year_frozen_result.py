"""Post-result E7-C frozen-receipt regression tests, no wildlife file reads."""
from __future__ import annotations

import json
import math
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "replication"
DATA = DOC / "E7_DIRECT_CAMERA_YEAR_FROZEN_RESULT_RECEIPT.json"


def read():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_single_extra_field_opening_is_provenanced_to_unchanged_prior_e7():
    r=read()
    x=r["execution"]
    assert r["status"]=="DIRECT_CELL_SUPPORT_LIMITED_NO_CROSS_PERIOD_SIGN_TRANSFER"
    assert x["new_distinct_postresult_run_id"]==40618416135
    assert x["workflow_conclusion"]=="success"
    assert x["synthetic_preflight_tests_passed"]==5
    assert x["artifact_id"]==12785339858
    assert x["artifact_zip_sha256"]=="65c09a20f9368f638c1d56ae8306650de3af6ebeedf2e443c728e76bf84f869f"
    assert x["original_result_json_sha256"]=="a032635e1acfabd89c253fe52308469735c4e13776ae3f49b7294cded9e7b6cf"
    assert x["raw_camera_or_sequence_identifiers_exported"] is False
    s=r["source"]
    assert s["all_11_source_sha256_verified"] is True
    assert s["all_11_per_season_QC_identical_to_original_E7"] is True
    assert s["original_E7_result_sha256"]=="21a0b03d8c17442ddeeed79023ec28d23525c2815ca7a0bbaf54faec12e65f2a"


def test_stricter_four_bin_eligibility_and_measured_support_loss():
    r=read()
    e=r["estimand"]
    assert e["original_frozen_taxa"]==12
    assert e["all_possible_unordered_species_pairs"]==66
    assert e["every_4_species_time_phase_counts_positive"] is True
    assert (e["min_complete_siteyears"],e["min_distinct_camera_names"],
            e["min_original_collection_season_folders"]) == (10,5,3)
    assert e["no_pseudocounts_or_response_adaptive_thresholds"] is True
    assert (r["discovery"]["estimable_pairs"],r["validation"]["estimable_pairs"]) == (1,9)
    assert (r["discovery"]["matched_siteyears_with_at_least_one_complete_species"],
            r["validation"]["matched_siteyears_with_at_least_one_complete_species"]) == (125,202)
    assert (r["transfer"]["original_E7_pooled_pair_MH_estimable_discovery"],
            r["transfer"]["original_E7_pooled_pair_MH_estimable_validation"]) == (54,50)


def test_only_shared_estimable_wildebeest_zebra_pair_does_not_transfer():
    r=read()
    a=r["discovery"]["sole_estimable_pair"]
    b=r["validation"]["sole_cross_period_eligible_pair"]
    assert (a["species_1"],a["species_2"]) == ("wildebeest","zebra")
    assert (b["species_1"],b["species_2"]) == ("wildebeest","zebra")
    assert (a["matched_siteyears"],a["distinct_cameras"]) == (19,18)
    assert (b["matched_siteyears"],b["distinct_cameras"]) == (46,40)
    assert math.isclose(a["median_local_log_relative_change"],1.3949078715028365,abs_tol=1e-12)
    assert math.isclose(b["median_local_log_relative_change"],-0.07287998051185596,abs_tol=1e-12)
    assert a["leave_one_camera"]["direction_stable"] is True
    assert b["sign_stable"] is False
    assert b["leave_one_camera_min_median"] < 0 < b["leave_one_camera_max_median"]
    assert r["transfer"]["pairs_estimable_in_both"] == 1
    assert r["transfer"]["same_direction_pairs"] == 0
    assert r["transfer"]["both_periods_leave_one_camera_sign_robust"] == 0


def test_local_three_taxon_closure_is_tautological_not_evidence_for_interactions():
    r=read()
    d=r["discovery"]["within_cell_identity"]
    v=r["validation"]["within_cell_identity"]
    assert (d["three_species_matched_camera_years"],
            d["checked_three_species_relations"]) == (24,85)
    assert (v["three_species_matched_camera_years"],
            v["checked_three_species_relations"]) == (39,137)
    assert d["maximum_absolute_triangle_gap"] < 1e-12
    assert v["maximum_absolute_triangle_gap"] < 1e-12
    x=r["science_limits"]
    assert x["local_same_camera_year_triangle_identity_is_algebraic_not_ecological"] is True
    assert x["biological_competition_or_causal_temporal_niches_not_identified"] is True
    assert x["strict_complete_cell_support_reduces_estimability"] is True
    assert x["absence_of_frozen_E7_MH_effects_is_not_established"] is True


def test_new_secondary_field_endpoint_does_not_change_previous_gate_or_result():
    r=read()
    x=r["science_limits"]
    assert x["exploratory_reopening_of_existing_E7_data"] is True
    assert x["new_external_independent_field_replication"] is False
    assert x["species_specific_camera_detection_uncalibrated"] is True
    assert x["weather_NDVI_or_plant_resources_not_measured"] is True
    assert x["E4_original_fit_scores_unchanged"] is True
    assert x["E5_original_qualified_datasets"] == 0
    assert x["E5_G4_passed"] is False
    md=(DOC/"E7_DIRECT_CAMERA_YEAR_DIEL_EMPIRICAL_SYNTHESIS.md").read_text(encoding="utf-8")
    assert "1/66" not in md or "66" in md
    assert "not proof" in md.lower()
    assert "not a" in md.lower()
    assert "without zero-cell modeling" in md.lower()
