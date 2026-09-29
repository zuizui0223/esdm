from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E3_MICA_ODSP_SERIALIZATION_CONTRACT.json"


def test_e3_odsp_serialization_is_parallel_and_not_population_handoff():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["required_source_status"] == "E3_EXPLORATORY_RESULT"
    assert contract["required_sampling_gate_passed"] is True
    assert contract["required_heldout_rows"] == 733

    rows = contract["row_semantics"]
    assert rows["group_count"] == 1
    assert rows["block_count"] == 733
    assert rows["endpoint_group"] == "MICA_MUSKRAT"

    ordering = contract["ordering_boundary"]
    assert ordering["natural_order_between_activity_and_state"] is False
    assert ordering["combined_three_level_filtration_authorized"] is False

    inference = contract["inference_boundary"]
    assert inference["analysis_mode"] == "descriptive"
    assert inference["n3_population_handoff_authorized"] is False
    assert inference["population_result_should_not_be_interpreted_as_superpopulation_value"] is True
    assert inference["odsp_certification_is_within_endpoint_block_resampling_only"] is True


def test_e3_odsp_serialization_keeps_claims_exploratory():
    claims = json.loads(CONTRACT.read_text(encoding="utf-8"))["claims"]

    assert claims["exploratory_activity_predictive_information_only"] is True
    assert claims["exploratory_state_predictive_information_only"] is True
    assert claims["independently_calibrated_state_effect"] is False
    assert claims["confirmatory_replication"] is False
    assert claims["causal_activity"] is False
    assert claims["causal_state"] is False
    assert claims["e2_rescue"] is False
