import json
from pathlib import Path


def test_external_camtrapdp_audit_is_independent_and_nonrescuing():
    contract = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "replication"
            / "CAMTRAPDP_EXTERNAL_TEMPORAL_AUDIT_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["programme_class"] == (
        "independent_external_data_contract_replication"
    )
    assert contract["source"]["doi"] == "10.5281/zenodo.11440456"
    assert contract["source"]["pilot"] == "pilot2"
    assert contract["source"]["expected_md5"] == (
        "ac94e6e646c5702f67d939ea9a059641"
    )
    assert contract["frozen_rule"]["no_padding"] is True
    assert contract["frozen_rule"]["no_timestamp_repair"] is True
    assert contract["prohibited"]["ecological_model_fit"] is True
    assert contract["prohibited"]["heldout_scoring"] is True
    assert contract["prohibited"]["change_to_first_empirical_result"] is True
