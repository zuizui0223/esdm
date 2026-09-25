import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07H_DIAGNOSTIC.json"
        ).read_text(encoding="utf-8")
    )


def test_v07h_deterministic_control_matches_expected_records():
    payload = _payload()

    assert payload["status"] == "FROZEN_DIAGNOSTIC"
    assert payload["run_id"] == 36106319723
    assert payload["expected_count_relative_error"] < 1e-12
    assert payload["selected"]["expected_direct_count"] == 931.25
    assert abs(payload["baseline"]["expected_direct_count"] - 931.25) < 1e-10
    assert payload["selected_to_baseline_worst_sd_ratio"] < 0.74
    assert payload["selected_to_baseline_effort_ratio"] < 0.74
    assert payload["artifact"]["github_digest"] == (
        "sha256:8f3092876bc867a11cb90e7632b79bbd5ab471cea424477767fbb2657788d40c"
    )
