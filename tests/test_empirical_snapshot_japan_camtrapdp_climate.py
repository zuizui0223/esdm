import json
from pathlib import Path


def test_snapshot_japan_camtrapdp_climate_is_response_blind_and_frozen():
    contract = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "empirical"
            / "SNAPSHOT_JAPAN_CAMTRAPDP_CLIMATE_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["candidate"]["camtrapdp_zenodo_record"] == 15030971
    assert contract["candidate"]["camtrapdp_file"] == "oo_1246258.zip"
    assert contract["candidate"]["camtrapdp_md5"] == (
        "742f186013ef3b60e9754df73e5269de"
    )
    assert contract["candidate"]["camtrapdp_response_opened"] is False
    assert contract["safe_geometry_source"]["expected_training_count"] == 70
    assert contract["safe_geometry_source"]["expected_heldout_count"] == 20
    assert contract["climate_source"]["member"] == "wc2.1_10m_bio_12.tif"
    assert contract["preprocessing"]["training_standardization_only"] is True
    assert contract["firewall"]["camtrapdp_archive_requests"] == 0
    assert contract["firewall"]["camtrapdp_response_rows_opened"] == 0
    assert contract["firewall"]["camtrapdp_response_values_opened"] is False
