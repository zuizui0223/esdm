import json
from pathlib import Path


def test_algar_header_contract_preserves_empirical_firewall():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs" / "empirical" / "ALGAR_HEADER_CONTRACT.json"
    )
    contract = json.loads(path.read_text(encoding="utf-8"))

    assert contract["scientific_freeze"]["r5b_status"] == "PASS"
    assert contract["dataset"]["response_rows_opened_by_esdm_before_gate"] == 0
    assert contract["dataset"]["response_values_opened_by_esdm_before_gate"] is False
    assert contract["prospective_biology"]["state_space"] == [
        "travelling",
        "secure",
    ]
    assert contract["header_transport"]["max_requests"] == 1
    assert contract["header_transport"]["max_header_bytes"] == 4096
    assert contract["header_transport"]["response_data_rows_allowed"] == 0
    assert contract["header_transport"]["model_fits_allowed"] == 0
    assert contract["header_stage"]["data_row_access_after_header_allowed"] is False
