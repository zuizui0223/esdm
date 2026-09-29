from __future__ import annotations

from pathlib import Path

import pytest

from scripts.freeze_e3_mica_infrastructure_stop import (
    freeze_infrastructure_stop,
)


def _valid():
    return dict(
        workflow_run_id=36522315963,
        run_attempt=1,
        head_sha="65300be9ab5ea25cbd321011c6e4ca1db7efc5f3",
        head_branch="explore/e3-mica-reduced-fit-run-v1",
        run_status="completed",
        run_conclusion="timed_out",
        artifact_count=0,
    )


def test_e3_infrastructure_stop_freezes_only_exact_authorized_run():
    receipt = freeze_infrastructure_stop(**_valid())

    assert receipt["status"] == "E3_EXPLORATORY_INFRASTRUCTURE_STOP"
    assert receipt["scientific_result_available"] is False
    assert receipt["scored_result_available"] is False
    assert receipt["execution"]["workflow_run_id"] == 36522315963
    assert receipt["execution"]["run_attempt"] == 1
    assert receipt["execution"]["canonical_result_artifact_count"] == 0


def test_e3_infrastructure_stop_forbids_rerun_and_downstream_promotion():
    receipt = freeze_infrastructure_stop(**_valid())

    assert receipt["decision"]["same_programme_rerun_allowed"] is False
    assert receipt["decision"]["confirmatory_replication_claim"] is False
    assert receipt["decision"]["e2_rescue"] is False
    assert receipt["terminal_rule"]["same_programme_rerun_allowed"] is False
    assert receipt["terminal_rule"]["post_result_threshold_retuning_allowed"] is False
    assert receipt["terminal_rule"]["post_result_stream_retuning_allowed"] is False
    assert receipt["terminal_rule"]["population_transfer_value_authorized"] is False
    assert receipt["terminal_rule"]["odsp_audit_authorized"] is False


def test_e3_infrastructure_stop_rejects_noncompleted_run():
    args = _valid()
    args["run_status"] = "in_progress"

    with pytest.raises(ValueError, match="completed run"):
        freeze_infrastructure_stop(**args)


def test_e3_infrastructure_stop_rejects_existing_result_artifact():
    args = _valid()
    args["artifact_count"] = 1

    with pytest.raises(ValueError, match="zero canonical result artifacts"):
        freeze_infrastructure_stop(**args)


def test_e3_infrastructure_stop_rejects_wrong_authorization_identity():
    args = _valid()
    args["head_sha"] = "a" * 40

    with pytest.raises(ValueError, match="head_sha mismatch"):
        freeze_infrastructure_stop(**args)
