from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADJ = ROOT / "docs" / "replication" / "E5_QLD_DEPLOYMENT_CAPTURE_ADJUDICATION.json"
RECEIPT = ROOT / "docs" / "replication" / "E5_QLD_DEPLOYMENT_CAPTURE_RECEIPT.json"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_qld_capture_stop_is_transport_only_and_response_blind():
    value = _read(ADJ)
    assert value["adjudication"]["status"] == (
        "E5_QLD_DEPLOYMENT_CAPTURE_TERMINAL_TRANSPORT_STOP"
    )
    assert value["adjudication"]["geometry_available"] is False
    assert value["adjudication"]["next_same_authorization_retry_allowed"] is False
    assert value["response_boundary"]["observation_rows_read"] == 0
    assert value["response_boundary"]["media_rows_read"] == 0
    assert value["response_boundary"]["species_fields_read"] == 0
    assert value["response_boundary"]["focal_response_opened"] is False


def test_qld_capture_receipt_pins_authorized_artifact():
    value = _read(RECEIPT)
    source = value["source_execution"]
    assert value["status"] == "FROZEN_TERMINAL_TRANSPORT_STOP_NO_METADATA_READ"
    assert source["workflow_run_id"] == 37120434627
    assert source["artifact_id"] == 11273134334
    assert source["capture_json_sha256"] == (
        "7de74a56dcf83b283f8c3ab4667a077bb6582e2787e3ae19d8c12480d072055f"
    )
    assert source["adjudication_json_sha256"] == (
        "982aa0b1bb361f4b63bb0625e034f927ee598480eee24448ea571ffb27d3fd61"
    )
    assert value["governance"]["same_authorization_retry_allowed"] is False
    assert value["governance"]["candidate_scientific_status_changed"] is False


def test_registry_tracks_qld_as_transport_blocked_not_qualified():
    reg = _read(REGISTRY)
    qld = next(
        x for x in reg["candidates"]
        if x["candidate_id"] == "qld_wet_tropics_camtrapdp_2022_2023"
    )
    assert qld["decision"] == "E5_CANDIDATE_NOT_YET_QUALIFIED_TRANSPORT_BLOCKED"
    assert qld["response_opened"] is False
    assert qld["public_metadata"]["collections_queried"] == 0
    assert qld["response_may_be_opened_for_E5"] is False
    assert reg["current_conclusion"]["qualified_candidate_count"] == 0
    assert reg["current_conclusion"]["strongest_current_named_candidate"] == (
        "qld_wet_tropics_camtrapdp_2022_2023"
    )
