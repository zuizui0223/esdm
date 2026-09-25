from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "validation" / "V07E_FROZEN_RESULTS.json"


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_v07e_frozen_result_pins_unique_authorized_run_and_artifact():
    result = _read()

    assert result["status"] == "PASS"
    assert result["outcome_run_id"] == 36088717290
    assert result["outcome_run_attempt"] == 1
    assert result["outcome_head_sha"] == "0ca249e3acaadc69eace3166970f4bf6619924ab"
    assert result["authorization_consumed_commit"] == (
        "7ad69a32f92c0cf3939e878b4fd0cb0a9ef957bc"
    )
    assert result["gate_freeze_commit"] == (
        "a047fdb0fd7843b83169d5b168d86de005143c3b"
    )
    assert result["gate_merge_commit"] == (
        "0e2c1f7b994f2a505f044030cfd057b871e217ef"
    )
    assert result["result_artifact"]["id"] == 10844319589
    assert result["result_artifact"]["github_digest"] == (
        "sha256:e4b0c42dfff5442f1ac388b55cba296db0c2d66dfde1ff93b3c99a26e0db3dcc"
    )
    assert result["result_artifact"]["result_json_sha256"] == (
        "2f186f74d315d54ea76e3676a64870c79d858630f20b6b5872d869cdb169c92e"
    )


def test_v07e_reciprocal_static_world_passes_all_frozen_checks():
    result = _read()
    summary = result["summary"]

    assert result["gate"] == {
        "passed": True,
        "checks_passed": 9,
        "checks_total": 9,
    }
    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert summary["static_better_rate"] == 1.0
    assert summary["mean_static_gain"] == 13.892651788335677
    assert summary["minimum_static_gain"] == 8.148554109093809
    assert summary["total_divergences"] == 0
    assert summary["mean_divergences_per_fit"] == 0.0


def test_v07d_v07e_pair_supports_reciprocal_resolution_specificity():
    pair = _read()["reciprocal_pair"]

    assert pair["v07d_dynamic_world"]["dynamic_better_rate"] == 1.0
    assert pair["v07d_dynamic_world"]["mean_dynamic_gain"] > 0
    assert pair["v07e_static_world"]["static_better_rate"] == 1.0
    assert pair["v07e_static_world"]["mean_static_gain"] > 0
    assert pair["reciprocal_specificity_supported"] is True


def test_v07e_result_remains_model_representation_not_odsp_transfer():
    boundary = _read()["interpretation_boundary"]

    assert boundary["equal_parameter_count_comparison"] is True
    assert boundary["same_observation_programme"] is True
    assert boundary["generator_is_static_quadratic"] is True
    assert boundary["reciprocal_model_resolution_specificity_supported"] is True
    assert boundary["universal_model_superiority"] is False
    assert boundary["movement_kernel_identified"] is False
    assert boundary["empirical_biological_validity"] is False
    assert boundary["odsp_information_transfer_source"] is False


def test_v07e_authorization_marker_is_not_present_in_frozen_result_branch():
    assert not (
        ROOT / "docs" / "validation" / "V07E_RUN_AUTHORIZED"
    ).exists()
