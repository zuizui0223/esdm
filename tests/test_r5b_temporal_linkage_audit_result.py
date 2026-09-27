import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "replication"
            / "R5B_TEMPORAL_LINKAGE_AUDIT_RESULT.json"
        ).read_text(encoding="utf-8")
    )


def test_temporal_audit_freezes_nonisolated_end_boundary_pattern():
    payload = _payload()

    assert payload["status"] == "AUDIT_COMPLETE"
    assert payload["programme_class"] == "separately_named_replication_audit"
    assert payload["all_animal_events"]["event_count"] == 7620
    assert payload["all_animal_events"]["interval_violation_count"] == 13
    assert payload["all_animal_events"]["before_start_count"] == 0
    assert payload["all_animal_events"]["after_end_count"] == 13
    assert payload["focal_cervus_nippon_events"]["event_count"] == 1430
    assert payload["focal_cervus_nippon_events"]["interval_violation_count"] == 4
    assert "7815128" in payload["focal_cervus_nippon_events"][
        "violation_event_ids"
    ]


def test_temporal_audit_does_not_reclassify_first_empirical_endpoint():
    interpretation = _payload()["interpretation"]

    assert interpretation["terminal_event_7815128_is_not_isolated"] is True
    assert interpretation["violations_are_all_after_deployment_end"] is True
    assert interpretation["all_detected_violations_within_24_hours"] is True
    assert interpretation["broad_timestamp_system_failure_supported"] is False
    assert interpretation["repair_or_exclusion_authorized"] is False
    assert interpretation["first_empirical_result_modified"] is False
    assert interpretation["model_fits"] == 0
    assert interpretation["heldout_scores"] == 0
