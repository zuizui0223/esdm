from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs"/"replication"
QC=DIR/"E5_WILDPIG_CA_LOCATIONNAME_QC_RESULT_RECEIPT.json"
OUTCOME=DIR/"E5_WILDPIG_ACTIVITY_ANCHOR_OUTCOME_RECEIPT.json"
TERMINAL=DIR/"E5_WILDPIG_ACTIVITY_ANCHOR_TERMINAL_RESULT.json"
REGISTRY=DIR/"E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_qc_receipt_matches_exact_single_run_and_real_source_blob():
    q=read(QC)
    s=q["source"]
    assert q["status"]=="PERSISTENT_RAW_LABEL_GRANULARITY_CONFLICT"
    assert s["original_one_shot_run_id"]==37643401531
    assert s["diagnostic_run_id"]==37706547653
    assert s["diagnostic_artifact_id"]==11519564272
    assert s["zip_sha256"]=="854cfd57c0df5cfd6db4bd37086c48ce6937abf458ba7c7c6dc1ae2a71da7fee"
    assert s["result_json_sha256"]=="60bafdcf4ed0d716dc4e5e8887abb8e9ac8b18661156dd8e4309f332dd6d053e"


def test_summer_label_anomaly_survives_trim_case_and_winter_has_missing_ids():
    q=read(QC)
    s=q["summary"]
    assert s["ca_spring"]["raw_unique_ids"]==48
    assert s["ca_fall"]["raw_unique_ids"]==48
    assert s["ca_summer"]["raw_unique_ids"]==434
    assert s["ca_summer"]["normalized_unique_ids"]==434
    assert s["ca_summer"]["singletons"]==383
    assert s["ca_summer"]["shared_with_any_other_season"]==48
    assert s["ca_summer"]["exclusive_to_summer"]==386
    assert s["ca_winter"]["raw_unique_ids"]==47
    assert s["ca_winter"]["blank_or_missing_location_id_rows"]==194
    assert s["ca_winter"]["all_rows"]-194==s["frozen_original_ca_winter_camera_events"]


def test_frozen_original_statistic_unresolved_and_quality_hold_are_distinct():
    o=read(OUTCOME)
    t=read(TERMINAL)
    assert o["execution"]["run_id"]==37643401531
    assert o["adjudication"]["frozen_result_status"]=="UNRESOLVED"
    assert o["adjudication"]["total_transfers"]==8
    assert o["adjudication"]["bootstrap_replicates"]==1000
    assert o["adjudication"]["point_positive_gain_count"]==6
    assert o["adjudication"]["bootstrap_median_gain_ci_lower"] < 0
    assert o["adjudication"]["bootstrap_median_gain_ci_upper"] > 0
    assert o["quality_audit"]["status"]=="HOLD_SAMPLE_IDENTITY"
    assert o["quality_audit"]["camera_cluster_bootstrap_validated"] is False
    assert t["status"]=="UNRESOLVED"
    assert t["quality_status"]=="HOLD_SAMPLE_IDENTITY"
    assert len(t["transfer_gain_summary"])==8
    assert t["claim_boundary"]["quality_qualified_empirical_conclusion"] is False


def test_registry_discloses_empirical_opening_only_in_alternative_route():
    v=read(REGISTRY)
    row=next(x for x in v["candidates"] if x["candidate_id"]=="wolfson_wildpig_gps_camera_2015_2018")
    assert v["current_conclusion"]["screened_candidate_count"]== 17
    assert v["current_conclusion"]["qualified_candidate_count"]==0
    assert v["current_conclusion"]["strongest_current_named_candidate"]=="rhode_island_paired_cameras_2018_2023"
    assert row["response_opened"] is True
    assert row["response_opened_under_route"]=="e5-external-activity-anchor-v1"
    assert row["response_opened_for_original_standard_E5"] is False
    assert row["response_may_be_opened_for_E5"] is False
    assert row["activity_anchor_route"]["empirical_outcome_status"]=="UNRESOLVED"
    assert row["activity_anchor_route"]["quality_status"]=="HOLD_SAMPLE_IDENTITY"
    assert row["activity_anchor_route"]["no_rerun"] is True
    assert row["gates"]["G4_DETECTION_IDENTIFIABILITY"].startswith("NOT_PASSED_DIRECT_DETECTION_ROUTE")


def test_qc_cannot_repair_original_model_or_claim_causal_mechanism():
    q=read(QC)
    o=read(OUTCOME)
    t=read(TERMINAL)
    assert q["conclusions"]["original_result_recomputed"] is False
    assert q["conclusions"]["original_one_shot_rerun"] is False
    assert q["conclusions"]["site_identity_mapping_to_48_cameras_available"] is False
    assert q["access_boundary"]["this_diagnostic_is_response_blind"] is False
    assert o["absolute_detection_probability_claim"] is False
    assert o["standard_E5_G4_passed"] is False
    assert t["claim_boundary"]["causal_sensor_mechanism_claim"] is False
    assert t["standard_e5"]["candidate_qualified"] is False
