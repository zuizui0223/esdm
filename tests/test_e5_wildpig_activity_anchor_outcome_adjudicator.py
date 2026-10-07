from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.adjudicate_e5_wildpig_activity_anchor_outcome import adjudicate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_WILDPIG_ACTIVITY_ANCHOR_POSTOUTCOME_CONTRACT.json"


def _contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _result(lower=-0.01, upper=0.02, status="UNRESOLVED"):
    transfers = []
    for i in range(8):
        transfers.append(
            {
                "training_geography": "FL" if i < 4 else "CA",
                "heldout_geography": "CA" if i < 4 else "FL",
                "season": ["spring", "summer", "fall", "winter"][i % 4],
                "baseline_overlap": 0.7,
                "corrected_overlap": 0.71,
                "gain": 0.01,
                "bootstrap_ci_lower": -0.02,
                "bootstrap_ci_upper": 0.04,
            }
        )
    return {
        "route_id": "e5-external-activity-anchor-v1",
        "result_id": "e5-wildpig-activity-anchor-transfer-result-v1",
        "status": status,
        "route_boundary": {
            "original_G4_passed": False,
            "absolute_detection_probability_identified": False,
            "abundance_identified": False,
            "causal_sensor_mechanism_identified": False,
            "untouched_preregistration": False,
        },
        "observed_sample_structure": {"FL_spring": {"gps_individuals": 10}},
        "point_transfers": transfers,
        "primary_summary": {
            "point_median_gain": 0.01,
            "point_minimum_gain": -0.01,
            "point_positive_gain_count": 5,
            "total_transfers": 8,
            "bootstrap_median_gain_ci_lower": lower,
            "bootstrap_median_gain_ci_upper": upper,
            "interpretation": status,
        },
        "bootstrap": {"replicates": 1000},
        "claim_boundary": {
            "original_E5_G4_pass_claim": False,
            "absolute_detection_claim": False,
            "abundance_claim": False,
            "causal_sensor_mechanism_claim": False,
        },
    }


@pytest.mark.parametrize(
    "lower,upper,status",
    [
        (0.001, 0.05, "SUPPORTED"),
        (-0.05, -0.001, "CONTRADICTED"),
        (-0.01, 0.02, "UNRESOLVED"),
        (0.0, 0.02, "UNRESOLVED"),
        (-0.02, 0.0, "UNRESOLVED"),
    ],
)
def test_frozen_ci_mapping_is_mechanical(lower, upper, status):
    result = _result(lower, upper, status)
    receipt, terminal = adjudicate(
        result,
        _contract(),
        run_id=1,
        job_id=2,
        artifact_id=3,
        artifact_digest="sha256:abc",
        result_sha256="def",
    )
    assert receipt["adjudication"]["frozen_result_status"] == status
    assert terminal["status"] == status
    assert terminal["standard_e5"]["candidate_qualified"] is False
    assert terminal["standard_e5"]["original_G4_reclassified"] is False


def test_status_mismatch_is_rejected():
    with pytest.raises(ValueError, match="result status"):
        adjudicate(
            _result(0.01, 0.02, "UNRESOLVED"),
            _contract(),
            run_id=1,
            job_id=2,
            artifact_id=3,
            artifact_digest="sha256:abc",
            result_sha256="def",
        )


def test_transfer_subset_is_rejected():
    value = _result()
    value["point_transfers"] = value["point_transfers"][:7]
    value["primary_summary"]["total_transfers"] = 7
    with pytest.raises(ValueError, match="transfer count"):
        adjudicate(
            value,
            _contract(),
            run_id=1,
            job_id=2,
            artifact_id=3,
            artifact_digest="sha256:abc",
            result_sha256="def",
        )


def test_claim_boundary_drift_is_rejected():
    value = _result()
    value["claim_boundary"]["absolute_detection_claim"] = True
    with pytest.raises(ValueError, match="absolute detection claim"):
        adjudicate(
            value,
            _contract(),
            run_id=1,
            job_id=2,
            artifact_id=3,
            artifact_digest="sha256:abc",
            result_sha256="def",
        )
