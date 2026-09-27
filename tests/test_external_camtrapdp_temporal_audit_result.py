import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "replication"
            / "CAMTRAPDP_EXTERNAL_TEMPORAL_AUDIT_RESULT.json"
        ).read_text(encoding="utf-8")
    )


def test_external_temporal_replication_freezes_zero_violation_result():
    payload = _payload()

    assert payload["status"] == "AUDIT_COMPLETE"
    assert payload["source"]["doi"] == "10.5281/zenodo.11440456"
    assert payload["source"]["pilot"] == "pilot2"
    assert payload["audit"]["deployment_count"] == 2
    assert payload["audit"]["unique_animal_event_count"] == 86
    assert payload["audit"]["unparseable_animal_event_rows_skipped"] == 0
    assert payload["audit"]["interval_violation_count"] == 0
    assert payload["audit"]["interval_violation_rate"] == 0.0


def test_external_temporal_replication_does_not_rewrite_first_endpoint():
    interpretation = _payload()["interpretation"]

    assert interpretation[
        "snapshot_japan_boundary_failure_replicated"
    ] is False
    assert interpretation[
        "exact_interval_rule_compatible_with_independent_camtrapdp_dataset"
    ] is True
    assert interpretation[
        "camtrapdp_standard_inherently_causes_boundary_violations_supported"
    ] is False
    assert interpretation[
        "universal_absence_of_boundary_violations_established"
    ] is False
    assert interpretation["model_fits"] == 0
    assert interpretation["heldout_scores"] == 0
    assert interpretation["first_empirical_endpoint_modified"] is False
