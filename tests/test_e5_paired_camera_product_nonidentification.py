from __future__ import annotations

import json
from pathlib import Path

from scripts.prove_e5_paired_camera_product_nonidentification import (
    expected_camera_rate,gauge_transform,normalized_shape,run_proof
)

ROOT=Path(__file__).resolve().parents[1]
PROOF=ROOT/"docs"/"replication"/"E5_RHODE_ISLAND_PAIRED_PRODUCT_NONIDENTIFICATION.json"


def test_synthetic_gauge_preserves_both_camera_means_but_changes_activity():
    a=[1.0,2.0,3.0]
    p=[0.2,0.4,0.3]
    e=[0.7,1.0,0.9]
    h=[1.2,2.0,1.5]
    anew,pnew=gauge_transform(a,p,h)
    before=expected_camera_rate(a,p,e)
    after=expected_camera_rate(anew,pnew,e)
    assert max(abs(x-y) for x,y in zip(before,after))<1e-12
    assert normalized_shape(a)!=normalized_shape(anew)


def test_response_free_two_sensor_counterexample_passes():
    result=run_proof()
    assert result["status"]=="PASS_NONIDENTIFICATION_WITNESS"
    assert result["max_observation_rate_error"]<1e-12
    assert result["max_relative_detection_ratio_error"]<1e-12
    assert result["max_normalized_activity_shape_difference"]>1e-3
    assert result["provenance"]["focal_response_rows_opened"] is False
    assert result["G4_pass_authorized"] is False


def test_necessity_of_extra_detection_information_keeps_G4_unpassed():
    contract=json.loads(PROOF.read_text(encoding="utf-8"))
    assert contract["status"]=="FROZEN_RESPONSE_FREE_NECESSARY_G4_OBLIGATION"
    assert contract["candidate_decision"].startswith("G4 REMAINS UNPASSED")
    assert len(contract["escape_routes_that_must_be_verified_before_final_G4"])==3
    assert contract["outcome_firewall"]["source_CSV_data_rows_opened"] is False
    assert contract["outcome_firewall"]["model_fitting_authorized"] is False
