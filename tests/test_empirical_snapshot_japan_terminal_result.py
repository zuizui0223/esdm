import json
from pathlib import Path


def _receipt():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "empirical"
            / "SNAPSHOT_JAPAN_CAMTRAPDP_TERMINAL_RESULT.json"
        ).read_text(encoding="utf-8")
    )


def test_first_empirical_opening_is_frozen_consumed_stop():
    result = _receipt()

    assert result["status"] == "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY"
    assert result["source"]["bytes_opened"] == 8630359
    assert result["source"]["md5"] == "742f186013ef3b60e9754df73e5269de"
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["activity_gain"] is None
    assert result["state_gain"] is None
    assert result["one_open_rule"]["response_consumed"] is True
    assert result["one_open_rule"]["retry_allowed"] is False
    assert result["one_open_rule"]["candidate_switch_allowed"] is False


def test_empirical_capture_artifact_provenance_is_frozen():
    result = _receipt()

    assert result["workflow_run_id"] == 36272212826
    assert result["artifact"]["id"] == 10916226656
    assert result["artifact"]["github_digest"] == (
        "sha256:16a658a1f1bf4512be054381a1f4bb8f71c016f81813d14c5428d6d49c002b0f"
    )
    assert result["source"]["sha256"] == (
        "2e99786857764151b66bfda0caaba4f23288ed9d671bb86c9ea5605727b9c07c"
    )
