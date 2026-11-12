"""Regression-lock source-verified, independent Safari14 spatial assemblage result.

Reads only the already frozen aggregate receipt and code. No wildlife ZIP,
photos, image timestamps, occupancy modeling or new biological opening.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "replication"
RECEIPT = EVIDENCE / "SAFARI14_SPATIAL_BETA_FROZEN_RESULT_RECEIPT.json"


def read() -> dict:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_source_and_one_shot_artifact_are_exactly_pinned():
    d=read()
    p=d["evidence_provenance"]
    assert d["status"]=="OBSERVED_TURNOVER_DOMINANCE_RECURS_IN_TWO_PROJECT_PARTITIONS"
    assert p["original_successful_workflow_run_id"]==42848095854
    assert p["successful_workflow_conclusion"]=="success"
    assert p["result_artifact_id"]==13779138089
    assert p["artifact_zip_sha256"]=="320d14fd10a191330d74f2a41a40ea2ccf8f94dee911224e96e6e0ec90b7a582"
    assert p["result_json_sha256"]=="f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7"
    assert p["original_source_zip_sha256"]=="2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1"
    assert p["one_shot_source_reopening_locked_to_successful_sha"] is True
    script=(ROOT/"scripts"/"safari14_spatial_beta.py").read_text(encoding="utf-8")
    assert p["original_source_zip_sha256"] in script


def test_exact_14_project_universe_and_12_only_eligible_park_ledger():
    d=read()
    q=d["input_coverage"]
    assert q["all_published_source_image_metadata_rows"]==4029374
    assert q["overlap_project_SER_excluded_images"]==1380098
    assert q["unrecognized_project_prefix_images_excluded"]==419158
    assert q["images_in_14_predeclared_non_SER_project_prefixes"]==2230118
    assert q["distinct_recorded_sequences_in_14_projects"]==1322887
    assert q["unique_physical_camera_location_keys"]==1153
    assert q["eligible_cameras_at_least_30_sequences"]==1106
    assert q["recognized_wild_mammal_annotation_rows"]==594868
    assert q["recognized_wild_mammal_label_categories"]==38
    assert q["no_wildlife_photos_downloaded"] is True
    s=d["preregistered_design"]
    assert len(s["project_codes_discovery"])==7
    assert len(s["project_codes_validation"])==7
    assert set(s["project_codes_discovery"]).isdisjoint(s["project_codes_validation"])
    assert s["project_station_metadata_unavailable_for_codes"]==["MLP","NIA"]
    a=d["actual_support"]
    assert len(a["discovery_eligible_projects"])==7
    assert len(a["validation_eligible_projects"])==5
    assert a["validation_ineligible_projects"]==["MLP","NIA"]
    assert (a["all_predeclared_pairs"],a["valid_eligible_project_pairs"])==(91,66)
    assert (a["discovery_pairs"],a["validation_pairs"],a["cross_partition_pairs"])==(21,10,35)
    assert sum(a["eligible_cameras_by_project"].values())==1106


def test_primary_both_partition_turnover_dominance_is_descriptive_not_every_pair():
    d=read()
    v=d["fixed_primary_comparisons"]
    assert v["original_predeclared_primary_decision_met"] is True
    for group,pairs,wins in (("discovery",21,11),("validation",10,6),("cross",35,16)):
        g=v[group]
        assert g["eligible_pairs" if group=="discovery" else (
            "eligible_pairs" if group=="validation" else "eligible_project_pairs"
        )]==pairs
        assert g["subsample_draws"]==500
        assert g["draws_with_median_turnover_exceeding_median_nestedness"]==500
        assert g["project_pairs_with_turnover_dominant_in_at_least_95pct_draws"]==wins
        assert g["median_projectpair_sim_over_draws"]>g["median_projectpair_sne_over_draws"]
        assert 0<=g["median_projectpair_sor_over_draws"]<=1
    exception=d["illustrative_individual_project_pair_exception"]
    assert (exception["project_1"],exception["project_2"])==("LEC","TSW")
    assert exception["pairwise_median_sim"]<exception["pairwise_median_sne"]
    assert math.isclose(exception["fraction_of_500_draws_turnover_exceeds_nestedness"],.206)


def test_claim_firewall_and_report_prevent_unsupported_temporal_or_causal_inference():
    d=read()
    c=d["interpretation_firewalls"]
    assert c["no_environmental_causes_or_pollinator_or_daynight_claims"] is True
    assert c["equal_cameras_and_min_sequences_do_not_control_operational_time_or_detection"] is True
    assert c["not_all_individual_project_pairs_consistently_turnover_dominated"] is True
    assert c["medians_of_components_need_not_sum_to_median_of_sorensen"] is True
    assert c["resampled_draws_are_not_independent_biological_replications"] is True
    assert c["E4_E5_E7_E7C_original_results_unmodified"] is True
    assert c["E5_original_qualified_datasets"]==0
    assert c["E5_G4_passed"] is False
    report=(EVIDENCE/"SAFARI14_SPATIAL_BETA_ECOLOGICAL_SYNTHESIS.md").read_text(encoding="utf-8")
    for key in ("500/500","11/21","6/10","0.206","MLP","NIA","not an inferential p-value"):
        assert key in report
