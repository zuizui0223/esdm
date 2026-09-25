import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07J_FROZEN_RESULTS.json"
        ).read_text(encoding="utf-8")
    )


def test_v07j_frozen_result_records_scientific_failure():
    payload = _payload()

    assert payload["status"] == "FAIL"
    assert payload["gate"]["passed"] is False
    assert payload["gate"]["checks_passed"] == 23
    assert payload["gate"]["checks_total"] == 25
    names = {row["name"] for row in payload["gate"]["failed_checks"]}
    assert names == {
        "transfer_positive:mean_ratio",
        "transfer_positive:winner_bias:sp.occupancy.epsilon_logit",
    }


def test_v07j_reversal_is_confirmed_despite_global_fail():
    payload = _payload()
    reversal = payload["summary"]["worlds"]["reversal"]

    assert reversal["correct_direction_rate"] == 0.9375
    assert reversal["mean_selected_to_baseline_ratio"] > 1.58
    assert reversal["total_divergences"] == 0
    assert payload["interpretation"]["reversal_detected"] is True


def test_v07j_fixed_schedule_is_not_promoted_as_transportable():
    payload = _payload()

    assert payload["interpretation"]["fixed_schedule_universally_transportable"] is False
    assert payload["interpretation"]["population_shift_requires_reoptimization_in_some_regions"] is True
    assert payload["interpretation"]["empirical_field_transportability_established"] is False
