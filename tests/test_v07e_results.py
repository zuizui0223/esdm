import json
from pathlib import Path


def _payload():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07E_FROZEN_RESULTS.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_v07e_frozen_result_passes_reciprocal_gate():
    payload = _payload()

    assert payload["status"] == "PASS"
    assert payload["gate"]["passed"] is True
    assert payload["gate"]["checks_passed"] == 9
    assert payload["gate"]["checks_total"] == 9

    summary = payload["summary"]
    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert summary["static_better_rate"] == 1.0
    assert summary["mean_static_gain"] > 13.0
    assert summary["minimum_static_gain"] > 9.0
    assert summary["total_divergences"] == 0


def test_v07e_artifact_provenance_and_reciprocal_pair_are_frozen():
    payload = _payload()

    assert payload["outcome_run_id"] == 36102363743
    assert payload["outcome_head_sha"] == (
        "beb373cca11d4c12a56558565e13159a5fc37767"
    )
    assert payload["gate_freeze_commit"] == (
        "3f542a4069bb77eda706e99347dda51414132ce9"
    )
    assert payload["gate_blob_sha"] == (
        "e4bc1e342808353f65067a2379c9813a13e867a4"
    )
    assert (
        payload["qualification_artifact"]["github_digest"]
        == "sha256:f434e06e55125e96e7301fb5fba3ea4b4e15eefd95bccdb20e88f02db4d7bba1"
    )
    assert (
        payload["result_artifact"]["github_digest"]
        == "sha256:e05fecc31d680b52fd84f85e21b4ee4243c7ba2cc7029e512976967c378803b5"
    )

    reciprocal = payload["reciprocal_pair"]
    assert reciprocal["v07d_dynamic_world_dynamic_better_rate"] == 1.0
    assert reciprocal["v07e_static_world_static_better_rate"] == 1.0
    assert reciprocal["bidirectional_resolution_discrimination_established"] is True


def test_v07e_cancelled_attempt_is_recorded_as_infrastructure_only():
    payload = _payload()
    superseded = payload["superseded_infrastructure_run"]

    assert superseded["run_id"] == 36088734964
    assert superseded["qualification_passed"] is True
    assert superseded["replicates_started"] is False
    assert payload["infrastructure_repair"]["scientific_settings_changed"] is False
