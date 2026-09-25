import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07F_FROZEN_RESULTS.json"
        ).read_text(encoding="utf-8")
    )


def test_v07f_frozen_result_passes_out_of_family_gate():
    payload = _payload()

    assert payload["status"] == "PASS"
    assert payload["gate"]["passed"] is True
    assert payload["gate"]["checks_passed"] == 13
    assert payload["gate"]["checks_total"] == 13
    assert payload["summary"]["replicates"] == 32
    assert payload["summary"]["fit_count"] == 64
    assert payload["summary"]["total_divergences"] == 0

    dynamic_like = payload["summary"]["worlds"]["dynamic_like"]
    static_like = payload["summary"]["worlds"]["static_like"]
    assert dynamic_like["correct_better_rate"] == 1.0
    assert dynamic_like["mean_correct_gain"] > 1.8
    assert dynamic_like["minimum_correct_gain"] > 0.0
    assert static_like["correct_better_rate"] == 1.0
    assert static_like["mean_correct_gain"] > 16.0
    assert static_like["minimum_correct_gain"] > 8.0


def test_v07f_artifact_provenance_is_frozen():
    payload = _payload()

    assert payload["outcome_run_id"] == 36104026876
    assert payload["outcome_head_sha"] == (
        "9303c3b8585e77d6da19bbe5535bc7aaa3651746"
    )
    assert payload["gate_freeze_commit"] == (
        "09a6ac71bcc1ddfc6781253e8b48aa377115e5d1"
    )
    assert payload["gate_blob_sha"] == (
        "092e3c706abe55912776f99fa5418e9ed205cc22"
    )
    assert payload["qualification_artifact"]["github_digest"] == (
        "sha256:792c0285a7eeba690cb234f4dd39f5222caf95a7cd93c5fabc9c73273ae35d3a"
    )
    assert payload["result_artifact"]["github_digest"] == (
        "sha256:c1aaf342efe834f07ce05427f9d8aa4bfaa62bf524ccaf3d9c7f2f7171f67610"
    )


def test_v07f_interpretation_boundary_records_out_of_family_support():
    boundary = _payload()["interpretation_boundary"]

    assert boundary["both_generators_outside_fitted_candidate_families"] is True
    assert boundary["out_of_family_temporal_resolution_robustness_established"] is True
    assert boundary["universal_misspecification_robustness"] is False
    assert boundary["empirical_biological_validity"] is False
