import json
from pathlib import Path


def test_r5b_temporal_linkage_audit_is_separate_and_nonrescuing():
    contract = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "replication"
            / "R5B_TEMPORAL_LINKAGE_AUDIT_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["programme_class"] == "separately_named_replication_audit"
    assert contract["scientific_parent"][
        "first_empirical_status_remains"
    ] == "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY"
    assert contract["scientific_parent"][
        "this_audit_cannot_modify_first_empirical_result"
    ] is True
    assert contract["frozen_integrity_rule"]["no_interval_padding"] is True
    assert contract["frozen_integrity_rule"]["no_row_deletion"] is True
    assert contract["frozen_integrity_rule"]["no_timestamp_repair"] is True
    assert contract["prohibited"]["model_fit"] is True
    assert contract["prohibited"]["heldout_scoring"] is True
    assert contract["prohibited"][
        "reclassification_of_first_empirical_endpoint"
    ] is True
    assert contract["execution"]["one_authorized_run"] is True
