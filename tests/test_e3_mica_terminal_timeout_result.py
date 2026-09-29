from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "replication" / "E3_MICA_REDUCED_TERMINAL_TIMEOUT_RESULT.json"


def _read() -> dict:
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_e3_terminal_timeout_locks_exact_execution_and_import_provenance():
    receipt = _read()

    assert receipt["receipt_id"] == "e3-mica-reduced-terminal-timeout-v1"
    assert receipt["authorization"]["workflow_run_id"] == 36522315963
    assert receipt["authorization"]["run_attempt"] == 1
    assert receipt["authorization"]["workflow_conclusion"] == "cancelled"
    assert receipt["failure"]["class"] == "INFRASTRUCTURE_TIMEOUT"
    assert receipt["failure"]["job_id"] == 109257663575
    assert receipt["failure"]["fit_step_number"] == 8
    assert receipt["failure"]["fit_step_conclusion"] == "cancelled"
    assert receipt["failure"]["workflow_timeout_minutes"] == 240
    assert receipt["failure"]["canonical_result_artifact_count"] == 0

    frozen = receipt["frozen_import"]
    assert frozen["workflow_run_id"] == 36543994633
    assert frozen["artifact_id"] == 11021587199
    assert frozen["artifact_digest"] == (
        "sha256:08c4515307fc7a8b7bab6c63093a6a9e36272531dca599f4d6561836b0ad40ee"
    )
    assert frozen["artifact_status"] == "E3_EXPLORATORY_INFRASTRUCTURE_STOP"


def test_e3_terminal_timeout_distinguishes_not_evaluated_from_failed():
    receipt = _read()
    scientific = receipt["scientific_result"]

    assert scientific["available"] is False
    assert scientific["activity_gain"] is None
    assert scientific["state_gain"] is None
    assert scientific["full_heldout_log_score"] is None
    assert scientific["activity_knockout_heldout_log_score"] is None
    assert scientific["state_knockout_heldout_log_score"] is None
    assert scientific["sampling_gate_evaluated"] is False
    assert scientific["sampling_gate_passed"] is None
    assert scientific["heldout_scores_serialized"] is False
    assert scientific["heldout_rows_serialized"] == 0


def test_e3_terminal_timeout_preserves_prefit_fixture_but_not_terminal_row_claims():
    receipt = _read()
    fixture = receipt["fixture_integrity"]

    assert fixture["prefit_qualified"] is True
    assert fixture["heldout_deployments_expected"] == 733
    assert fixture["capture_fixture_fingerprint_sha256"] == (
        "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
    )
    assert fixture["terminal_result_row_count_verified"] is False
    assert fixture["terminal_result_fixture_fingerprint_verified"] is False


def test_e3_terminal_timeout_forbids_rerun_retuning_and_scientific_promotion():
    receipt = _read()
    terminal = receipt["terminal_rule"]

    assert terminal["same_programme_rerun_allowed"] is False
    assert terminal["retuning_allowed"] is False
    assert terminal["replacement_fit_authorized"] is False
    assert terminal["odsp_audit_authorized"] is False
    assert terminal["population_transfer_value_authorized"] is False
    assert terminal["scientific_fail_interpretation_authorized"] is False
