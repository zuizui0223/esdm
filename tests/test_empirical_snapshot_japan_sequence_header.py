import json
from pathlib import Path


def test_snapshot_japan_sequence_header_is_exactly_frozen():
    contract = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "empirical"
            / "SNAPSHOT_JAPAN_SEQUENCE_HEADER_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["publisher_metadata"]["supplement_doi"] == (
        "10.3897/BDJ.13.e141168.suppl2"
    )
    assert contract["publisher_metadata"]["original_file_url"] == (
        "https://binary.pensoft.net/file/1165478"
    )
    assert contract["expected_header"] == [
        "project_id", "deployment_id", "sequence_id", "is_blank",
        "identified_by", "wi_taxon_id", "class", "order", "family",
        "genus", "species", "common_name", "uncertainty", "start_time",
        "end_time", "group_size", "age", "sex", "animal_recognisable",
        "individual_id", "individual_animal_notes", "behaviour",
        "highlighted", "markings", "cv_confidence", "licence"
    ]
    assert contract["focal_biology_frozen_before_header"]["species"] == (
        "Cervus nippon"
    )
    assert contract["focal_biology_frozen_before_header"]["state_space"] == [
        "adult", "juvenile"
    ]
    assert contract["header_transport"]["response_data_row_bytes_allowed"] == 0
    assert contract["firewall"]["data_row_access_after_header"] is False
