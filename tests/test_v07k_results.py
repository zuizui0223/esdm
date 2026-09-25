import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07K_FROZEN_RESULTS.json"
        ).read_text(encoding="utf-8")
    )


def test_v07k_frozen_result_records_scientific_failure():
    payload = _payload()

    assert payload["status"] == "FAIL"
    assert payload["gate"]["passed"] is False
    assert payload["gate"]["checks_passed"] == 23
    assert payload["gate"]["checks_total"] == 25
    names = {row["name"] for row in payload["gate"]["failed_checks"]}
    assert names == {
        "transfer_positive:adaptive_lower_worst_sd_rate",
        "transfer_positive:mean_worst_sd_ratio",
    }


def test_v07k_reversal_local_adaptation_is_strong():
    reversal = _payload()["summary"]["worlds"]["reversal"]

    assert reversal["adaptive_lower_worst_sd_rate"] == 1.0
    assert reversal["mean_worst_sd_ratio"] < 0.62
    assert reversal["oracle_placement_selection_rate"] == 0.75
    assert reversal["total_divergences"] == 0


def test_v07k_does_not_promote_universal_repiloting():
    payload = _payload()
    transfer = payload["summary"]["worlds"]["transfer_positive"]

    assert transfer["adaptive_lower_worst_sd_rate"] == 0.5625
    assert transfer["mean_worst_sd_ratio"] > 1.0
    assert payload["interpretation"]["local_adaptation_universally_incremental"] is False
    assert payload["interpretation"]["selective_repiloting_hypothesis_generated"] is True
