import json
from pathlib import Path


def test_snapshot_japan_gbif_transport_is_head_only():
    contract = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "empirical"
            / "SNAPSHOT_JAPAN_GBIF_TRANSPORT_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["dataset"]["gbif_dataset_key"] == (
        "f0a42d7d-1eda-4ec8-ac66-c1343acea3bc"
    )
    assert contract["dataset"]["doi"] == "10.15468/y4erss"
    assert contract["transport"]["method"] == "HEAD"
    assert contract["transport"]["max_requests"] == 1
    assert contract["transport"]["body_bytes_allowed"] == 0
    assert contract["firewall"]["response_payload_bytes"] == 0
    assert contract["firewall"]["response_rows_opened"] == 0
    assert contract["firewall"]["response_values_opened"] is False
