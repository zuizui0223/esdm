from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from scripts.prove_e5_external_activity_anchor_identification import (
    camera_shape,
    normalize_log_shape,
    recover_relative_distortion,
    run_proof,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_EXTERNAL_ACTIVITY_ANCHOR_IDENTIFICATION_CONTRACT.json"
ADJ=ROOT/"docs"/"replication"/"E5_WILDPIG_ACTIVITY_ANCHOR_HEADER_ADJUDICATION.json"
RECEIPT=ROOT/"docs"/"replication"/"E5_WILDPIG_GPS_CAMERA_HEADER_RECEIPT.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_header_receipt_preserves_zero_response_rows_and_pins_artifact():
    v=_read(RECEIPT)
    assert v["execution"]["workflow_run_id"]==37611608664
    assert v["execution"]["artifact_id"]==11477917856
    assert v["execution"]["result_json_sha256"]=="7d1463aeaf7ee8b50005bf0e0fe5c4466ec2187571703782ef79c4746513e584"
    assert v["response_boundary"]["data_rows_decoded"]==0
    assert v["response_boundary"]["focal_response_opened"] is False


def test_manual_header_adjudication_advances_A2_A4_without_original_G4_reclassification():
    v=_read(ADJ)
    gates={x["gate"]:x["status"] for x in v["route_gates"]}
    assert gates["A1_CROSSED_METHOD_GEOGRAPHY"]=="PASS"
    assert gates["A2_ACTIVITY_ANCHOR_SCHEMA"]=="PASS_MANUAL_HEADER_ADJUDICATION"
    assert gates["A3_CAMERA_SCHEMA"]=="PASS_ROUTE_LEVEL_NETWORK_EXPOSURE_WITH_CAVEAT"
    assert gates["A4_TEMPORAL_OVERLAP"]=="PASS_PUBLIC_METHODS"
    assert gates["A5_RELATIVE_DISTORTION_IDENTIFIABILITY"]=="PENDING_STRUCTURAL_PROOF"
    assert v["original_e5_status"]["G4_DETECTION_IDENTIFIABILITY"]=="NOT_PASSED_DIRECT_DETECTION_ROUTE"
    assert v["decision"]["data_row_opening_authorized"] is False


def test_relative_distortion_closed_form_recovers_normalized_shape():
    a=np.array([0.2,0.4,0.1,0.3])
    d_raw=np.array([0.5,2.0,1.0,4.0])
    d=normalize_log_shape(d_raw)
    c=camera_shape(a,d_raw)
    got=recover_relative_distortion(a,c)
    np.testing.assert_allclose(got,d,rtol=0,atol=1e-12)


def test_relative_distortion_is_invariant_to_raw_distortion_scale():
    a=np.array([1.0,3.0,2.0,4.0])
    d=np.array([0.4,1.2,3.0,0.7])
    one=recover_relative_distortion(a,camera_shape(a,d))
    two=recover_relative_distortion(a,camera_shape(a,99*d))
    np.testing.assert_allclose(one,two,rtol=0,atol=1e-12)


def test_response_free_A5_proof_passes_but_claims_only_relative_shape():
    v=run_proof()
    assert v["status"]=="PASS"
    assert v["decision"]["A5_structural_identifiability_pass"] is True
    assert v["decision"]["absolute_detection_probability_identified"] is False
    assert v["decision"]["abundance_identified"] is False
    assert v["response_boundary"]["empirical_values_opened"] is False


def test_identification_contract_forbids_empirical_opening_and_absolute_detection_claim():
    v=_read(CONTRACT)
    assert v["status"]=="FROZEN_RESPONSE_FREE_STRUCTURAL_PROOF"
    assert v["estimand"]["absolute_detection_probability_identified"] is False
    assert v["estimand"]["abundance_identified"] is False
    assert v["response_firewall"]["focal_camera_event_values_opened"] is False
    assert v["response_firewall"]["gps_location_values_opened"] is False
    assert v["response_firewall"]["model_fitting_authorized"] is False
