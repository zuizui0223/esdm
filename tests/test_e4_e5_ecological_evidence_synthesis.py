from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "replication"


def _read(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_ecological_synthesis_uses_terminal_e4_scores_and_uncertainty():
    e4 = _read("E4_MICA_POSTRESULT_SYNTHESIS.json")
    scores = e4["frozen_empirical_result"]["scores"]
    assert math.isclose(scores["activity_gain"], -0.6390511804117178, abs_tol=1e-13)
    assert math.isclose(scores["state_gain"], 0.008390925023042506, abs_tol=1e-13)
    blocks = e4["uncertainty_audits"]["physical_location_blocks"]
    assert blocks["block_count"] == 27
    assert blocks["activity"]["upper_bound"] < 0
    assert blocks["state"]["lower_bound"] < 0 < blocks["state"]["upper_bound"]
    geom = e4["failure_geometry"]["deployment_level"]
    assert geom["event_bearing_heldout_deployments"] == 128
    assert geom["event_bearing_negative_activity_gain"] == 127
    diel = e4["diel_domain_shift"]["cross_taxon_negative_control"]
    assert diel["nonfocal_eligible_species"] == 7
    assert diel["nonfocal_species_with_lower_ratio"] == 6
    assert e4["identifiability_limit"]["causal_behavioral_nonstationarity_identified"] is False


def test_wildpig_transfer_unresolved_with_physical_site_identity_hold():
    w = _read("E5_WILDPIG_ACTIVITY_ANCHOR_OUTCOME_RECEIPT.json")
    a = w["adjudication"]
    assert a["frozen_result_status"] == "UNRESOLVED"
    assert a["total_transfers"] == 8
    assert a["point_positive_gain_count"] == 6
    assert a["bootstrap_replicates"] == 1000
    assert a["bootstrap_median_gain_ci_lower"] < 0 < a["bootstrap_median_gain_ci_upper"]
    assert w["quality_audit"]["status"] == "HOLD_SAMPLE_IDENTITY"
    assert w["quality_audit"]["ca_summer_pseudo_site_clusters"] == 434
    assert w["standard_E5_G4_passed"] is False


def test_rhode_matched_deployments_do_not_imply_diel_detection_identification():
    r = _read("E5_RHODE_ISLAND_DEPLOYMENT_GEOMETRY_RECEIPT.json")
    assert r["deployment"]["valid_effort_rows"] == 2982
    assert r["deployment"]["site_identifiers_with_spatial_conflict"] == 1
    assert r["deployment"]["site_identifiers_with_consistent_coordinates"] == 264
    assert r["deployment"]["published_site_count"] == 249
    west = r["operational_blocks"]["WEST_OPERATIONAL"]
    east = r["operational_blocks"]["EAST_OPERATIONAL"]
    assert west["independent_site_IDs_with_valid_effort"] == 132
    assert east["independent_site_IDs_with_valid_effort"] == 132
    assert west["site_IDs_with_matched_camera_operational_overlap"] == 126
    assert east["site_IDs_with_matched_camera_operational_overlap"] == 120
    assert r["fixed_interpretation"]["G4"].startswith("NOT_PASSED")
    assert r["response_firewall"]["biological_response_rows_processed"] == 0


def test_findlay_descriptive_fox_stages_are_not_confirmatory_transfer():
    f = _read("E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json")
    cells = {
        (x["species"], x["distance_bin"]): x
        for x in f["stage_cells"]
    }
    near = cells[("FOX", "near_le_1m")]
    far = cells[("FOX", "far_gt_3m")]
    assert (near["cctv_reference_passes"], near["triggered_reference_passes"], near["registered_images"]) == (88, 55, 19)
    assert (far["cctv_reference_passes"], far["triggered_reference_passes"], far["registered_images"]) == (175, 47, 27)
    assert near["p_trigger"] > far["p_trigger"]
    assert near["p_registration_given_trigger"] < far["p_registration_given_trigger"]
    assert near["p_composite_given_pass"] > far["p_composite_given_pass"]
    assert f["quality_limits"]["inferential_confidence_intervals_authorized"] is False
    assert f["gate_boundary"]["original_standard_E5_qualified"] == 0

    linkage = _read("E5_FINDLAY_PASSAGE_LINKAGE_FORENSIC_RECEIPT.json")
    c = linkage["frozen_comparison"]
    assert c["trigger_csv_rows"] == c["registration_csv_rows"] == 881
    assert c["same_row_order_shared_covariate_signatures"] == 881
    assert c["same_row_order_trigger_flags"] == 881
    assert c["unique_shared_covariate_fingerprint_pairs"] == 530
    assert c["identical_but_ambiguous_duplicate_fingerprint_rows"] == 351
    assert c["internal_unique_passage_ID_linkage_verified"] is False
    assert linkage["interpretation"]["original_FOX_stage_descriptive_claim_promoted_to_confirmatory"] is False


def test_readme_and_synthesis_show_e5_boundary_not_new_ecological_discovery():
    registry = _read("E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json")
    assert registry["current_conclusion"]["screened_candidate_count"] == 17
    assert registry["current_conclusion"]["qualified_candidate_count"] == 0
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    synthesis = (DATA / "E4_E5_ECOLOGICAL_EVIDENCE_SYNTHESIS.md").read_text(encoding="utf-8")
    assert "E4_E5_ECOLOGICAL_EVIDENCE_SYNTHESIS.md" in readme
    assert "0/17" in readme and "0/17" in synthesis
    assert "UNRESOLVED" in readme and "UNRESOLVED" in synthesis
    assert "HOLD_SAMPLE_IDENTITY" in readme
    assert "does not" in synthesis.lower() or "not" in synthesis.lower()
    assert "no new fit" in synthesis.lower()
