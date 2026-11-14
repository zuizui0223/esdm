"""Frozen S14-FM outcome receipt checks; aggregate only, no source file reads."""
from __future__ import annotations

import json
import math
from pathlib import Path

DOC=Path(__file__).resolve().parents[1]/"docs"/"replication"


def read(name):
    return json.loads((DOC/name).read_text(encoding="utf-8"))


def test_original_and_new_sha256_provenance_and_one_source_opening():
    x=read("SAFARI14_FIXED_MARGINS_NULL_RESULT_RECEIPT.json")
    p=x["provenance"]
    assert p["empirical_action_run"]==43580142370
    assert p["successful_head_sha"]=="62b9d529d05c6ff1a14981d8705f4e0a5e828acb"
    assert p["artifact_id"]==14107094556
    assert p["artifact_zip_sha256"]=="a9f32536b4120c249abd57c59981e6cfcaab4deb19016b788a0000ac35bd06dc"
    assert p["inner_json_sha256"]=="4dcf8212510524dccefbfa250e05277fe55085f3b838c33a1c5f7fc8ee593b5e"
    assert p["original_safari_result_sha256"]=="f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7"
    assert p["original_source_zip_sha256"]=="2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1"
    assert p["original_500_camera_draws_and_91_pair_results_reconciled"] is True
    assert p["source_QC_reconciled"] is True
    assert p["synthetic_tests_passed_before_source_opening"]==6


def test_exactly_original_7_and_5_park_support_and_camera_row_column_margins():
    x=read("SAFARI14_FIXED_MARGINS_NULL_RESULT_RECEIPT.json")
    s=x["setup"]
    assert len(s["original_discovery_parks"])==7
    assert len(s["original_validation_parks"])==5
    assert s["original_missing_MLP_NIA_ineligibility_retained"] is True
    assert s["null_matrix_preserves_each_camera_species_richness"] is True
    assert s["null_matrix_preserves_each_species_positive_camera_count_within_partition"] is True
    assert s["draws_per_group"]==500
    assert s["burnin_trade_proposals_per_camera"]==30
    assert s["between_draw_trade_proposals_per_camera"]==15
    assert x["discovery"]["source_camera_rows"]==696
    assert x["validation"]["source_camera_rows"]==410
    assert x["discovery"]["positive_camera_species_incidences"]==4915
    assert x["validation"]["positive_camera_species_incidences"]==3508
    assert x["discovery"]["positive_taxa"]==x["validation"]["positive_taxa"]==36
    assert x["discovery"]["margins_preserved"] and x["validation"]["margins_preserved"]


def test_both_partitions_observed_excess_but_not_independent_significance():
    x=read("SAFARI14_FIXED_MARGINS_NULL_RESULT_RECEIPT.json")
    original=read("SAFARI14_SPATIAL_BETA_FROZEN_RESULT_RECEIPT.json")
    for g,count,mean_null,dominance,median_delta,pairs,positive_pairs in (
        ("discovery",696,.08333333333333333,18,.3888888888888889,21,19),
        ("validation",410,.11805555555555555,354,.23958333333333334,10,10)
    ):
        q=x[g]
        assert q["source_camera_rows"]==count
        assert math.isclose(q["fixed_margins_null_median_sim"],mean_null,abs_tol=1e-12)
        assert q["null_draws_with_sim_gt_sne"]==dominance
        assert math.isclose(q["median_paired_sim_excess"],median_delta,abs_tol=1e-12)
        assert q["fully_eligible_paired_draws"] if "fully_eligible_paired_draws" in q else q["complete_paired_draws"]==500
        assert q["observed_sim_gt_null_draws"]==500
        assert q["park_pairs_total"]==pairs
        assert q["park_pair_excess_positive"]==positive_pairs
        assert q["fixed_descriptive_criterion_passed"] is True
        assert q["observed_median_sim"] if "observed_median_sim" in q else True
        orig=original["fixed_primary_comparisons"][g]["median_projectpair_sim_over_draws"]
        assert math.isclose(q["observed_median_sim"],orig,abs_tol=1e-12)
    assert x["discovery"]["pair_exceptions"]==["CDB vs KAR","APN vs KRU"]
    assert x["validation"]["pair_exceptions"]==[]
    assert x["inference_bounds"]["no_ecological_null_pvalue_or_confidence_interval_claimed"] is True


def test_older_richness_only_counterexample_is_retained_not_silently_removed():
    prior=read("SAFARI14_STRUCTURAL_NULL_RESULT_RECEIPT.json")
    q=prior["scenarios"][0]
    assert q["alpha"]==0
    assert q["discovery_dominant"]==q["validation_dominant"]==500
    x=read("SAFARI14_FIXED_MARGINS_NULL_RESULT_RECEIPT.json")
    assert x["discovery"]["null_draws_with_sim_gt_sne"]==18
    assert x["validation"]["null_draws_with_sim_gt_sne"]==354
    assert x["inference_bounds"]["original_positive_camera_record_turnover_description_unchanged"] is True


def test_report_limits_detection_park_pool_and_causal_assembly_claims():
    x=read("SAFARI14_FIXED_MARGINS_NULL_RESULT_RECEIPT.json")
    b=x["inference_bounds"]
    assert b["no_independent_data_provider_replication"] is True
    assert b["park_to_park_camera_exchangeability_assumption_unverified"] is True
    assert b["biological_camera_operational_effort_and_detection_unmeasured"] is True
    assert b["no_ecological_null_pvalue_or_confidence_interval_claimed"] is True
    assert b["result_does_not_identify_causal_environmental_filtering_or_dispersal"] is True
    assert b["E5_original_qualified_datasets"]==0
    assert b["E5_original_G4_passed"] is False
    md=(DOC/"SAFARI14_FIXED_MARGINS_NULL_ECOLOGICAL_RESULT.md").read_text(encoding="utf-8")
    for token in ("500/500","19/21","10/10","0.3889","0.2396","not a formal", "not independently", "nonrandom"):
        assert token.lower() in md.lower()
