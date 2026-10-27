"""E7 terminal claim and evidence receipts: aggregate-only regression tests.

No camera archive download, wildlife image, individual location, fresh
biological outcome, model fitting, or second ecological-run authorization.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "replication"


def read(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_technical_restart_has_independently_verifiable_provenance():
    r = read("E7_SERENGETI_WET_DRY_FROZEN_RESULT_RECEIPT.json")
    p = r["empirical_provenance"]
    assert r["status"] == "EXPLORATORY_COMPLETED_NO_STABLE_SEASONAL_PAIR_REVERSAL_TRANSFER"
    assert p["original_format_failure_run_id"] == 39220306440
    assert p["technical_compatibility_success_run_id"] == 39222089646
    assert p["successful_workflow_conclusion"] == "success"
    assert p["original_result_artifact_id"] == 12173010259
    assert p["artifact_zip_sha256"] == "e210adc894a94827a295afba87ad72fa485e8721a65ca7db11c5931655e4edfe"
    assert p["artifact_json_sha256"] == "21a0b03d8c17442ddeeed79023ec28d23525c2815ca7a0bbaf54faec12e65f2a"
    assert p["claimed_untouched_one_shot"] is False
    previous = read("E7_SERENGETI_SOURCE_FORMAT_STOP.json")
    assert previous["biological_effect_estimates_produced"] == 0
    assert len(previous["source_file_sha256"]) == 11
    from scripts.e7_serengeti_wet_dry_diel import EXPECTED_SOURCE_SHA256
    assert previous["source_file_sha256"] == EXPECTED_SOURCE_SHA256


def test_frozen_roster_and_response_coverage_use_named_source_units():
    r = read("E7_SERENGETI_WET_DRY_FROZEN_RESULT_RECEIPT.json")
    c = r["input_scope"]
    assert c["published_collection_seasons"] == 11
    assert c["discovery_collection_seasons"] == [1,2,3,4,5]
    assert c["validation_collection_seasons"] == [6,7,8,9,10,11]
    assert c["aggregate_image_records"] == 7178440
    assert c["aggregate_annotation_rows"] == 7261545
    assert c["distinct_sequences_with_image_metadata"] == 2659222
    assert c["eligible_species_sequence_events_in_wet_or_dry_core_months"] == 494385
    assert c["eligible_species_sequence_events_in_frozen_night_or_midday_hours"] == 309945
    assert c["image_files_downloaded"] == 0
    s = r["frozen_selection"]
    assert len(s["fixed_roster"]) == s["panel_size"] == 12
    assert s["total_unordered_pairs"] == 66
    assert s["wet_core_months"] == [11,12,1,2,3,4]
    assert s["dry_core_months"] == [6,7,8,9]
    assert s["biological_effect_rules_changed_from_frozen_design"] is False


def test_discovery_and_holdout_results_must_not_promote_a_weak_transfer():
    r = read("E7_SERENGETI_WET_DRY_FROZEN_RESULT_RECEIPT.json")
    a,b,c = r["discovery"],r["validation"],r["temporal_transfer"]
    assert (a["estimable_pairs"],a["rank_reversals_across_wet_dry_recorded_odds"],
            a["single_camera_leave_one_out_stable_reversals"]) == (54,14,2)
    assert (b["estimable_pairs"],b["rank_reversals_across_wet_dry_recorded_odds"],
            b["single_camera_leave_one_out_stable_reversals"]) == (50,3,0)
    assert (c["estimable_in_both_partitions"],c["concordant_dry_vs_wet_effect_direction"],
            c["both_partitions_stable_rank_reversal"]) == (46,23,0)
    assert math.isclose(c["concordant_fraction"],23/46)
    assert c["tested_pairs_are_statistically_dependent"] is True
    assert c["no_inferential_pvalue_or_confidence_interval"] is True
    assert c["repeated_rank_reversal_same_direction"] == 1
    assert c["repeated_rank_reversal_same_direction_loo_robust"] is False
    for p in a["stable_pair_details"]:
        assert p["wet_relative_record_odds"] != p["dry_relative_record_odds"]
        assert p["validation_stable_reversal"] is False


def test_ecological_claims_and_legacy_result_are_not_implicitly_upgraded():
    r = read("E7_SERENGETI_WET_DRY_FROZEN_RESULT_RECEIPT.json")
    g = r["governance"]
    assert g["original_E4_fit_changed"] is False
    assert g["original_E5_G4_passed"] is False
    assert g["original_E5_qualified_candidates"] == 0
    assert g["terminal_interpretation_post_outcome_descriptive"] is True
    txt = (DATA / "E7_SERENGETI_WET_DRY_EMPIRICAL_SYNTHESIS.md").read_text(encoding="utf-8")
    for phrase in ("54", "50", "23/46", "zero", "E5", "not", "independent"):
        assert phrase.lower() in txt.lower()
