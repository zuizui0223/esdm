from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STOP = ROOT / "docs" / "replication" / "E2_MICA_TEMPORAL_INTEGRITY_INFRASTRUCTURE_STOP_V1.json"
R2 = ROOT / "docs" / "replication" / "E2_MICA_TEMPORAL_INTEGRITY_REPLACEMENT_R2.json"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_temporal_first_attempt_stopped_before_any_response_opening():
    stop = _read(STOP)

    assert stop["authorization"]["workflow_run_id"] == 36317883452
    assert stop["authorization"]["run_attempt"] == 1
    assert stop["authorization"]["conclusion"] == "failure"
    failure = stop["failure"]
    assert failure["stage"] == "authorization_precheck"
    assert failure["class"] == "INFRASTRUCTURE_ONLY"
    assert failure["candidate_archive_downloaded"] is False
    assert failure["observation_rows_scanned"] == 0
    assert failure["scientific_name_values_read"] is False
    assert failure["count_values_read"] is False
    assert failure["model_fits"] == 0
    assert failure["heldout_scores"] == 0
    assert failure["temporal_outcome_consumed"] is False


def test_temporal_r2_changes_only_execution_infrastructure():
    amendment = _read(R2)

    assert amendment["status"] == "FROZEN_INFRASTRUCTURE_REPLACEMENT"
    changes = amendment["scientific_changes"]
    assert all(value is False for value in changes.values())

    execution = amendment["replacement_execution"]
    assert execution["branch"] == "e2/mica-temporal-integrity-v1-r2"
    assert execution["authorization_marker"].endswith(
        "E2_MICA_TEMPORAL_INTEGRITY_AUTHORIZED_R2.json"
    )
    assert execution["checkout_fetch_depth"] == 0
    assert execution["one_shot"] is True
    assert execution["workflow_dispatch_enabled"] is False

    governance = amendment["governance"]
    assert governance["original_failed_authorization_not_reused"] is True
    assert governance["new_authorization_commit_must_be_pure"] is True
    assert governance["archive_download_forbidden_before_precheck_passes"] is True
    assert governance["full_response_authorized"] is False
