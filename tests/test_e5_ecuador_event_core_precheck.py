from __future__ import annotations

import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_ecuador_event_core import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_ECUADOR_EVENT_CORE_PRECHECK_CONTRACT.json"
)


META = """<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <core encoding="UTF-8" fieldsTerminatedBy="\t" linesTerminatedBy="\n"
        ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Event">
    <files><location>event.txt</location></files>
    <id index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/parentEventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/locationID"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/samplingProtocol"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/sampleSizeValue"/>
    <field index="8" term="http://rs.tdwg.org/dwc/terms/sampleSizeUnit"/>
  </core>
  <extension encoding="UTF-8" fieldsTerminatedBy="\t" linesTerminatedBy="\n"
             ignoreHeaderLines="1"
             rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files><location>occurrence.txt</location></files>
    <coreid index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
  </extension>
</archive>
"""


def _archive(path: Path, *, response_term_in_core: bool = False):
    meta = META
    event = (
        "eventID\tparentEventID\teventDate\tlocationID\tdecimalLatitude\t"
        "decimalLongitude\tsamplingProtocol\tsampleSizeValue\tsampleSizeUnit\n"
        "e1\t\t2020-01-01/2020-01-31\tl1\t-1.0\t-78.0\tcamera trap\t30\tdays\n"
        "e2\te1\t2020-06-01/2020-06-30\tl2\t-2.0\t-79.0\tcamera trap\t30\tdays\n"
    )
    if response_term_in_core:
        meta = meta.replace(
            '<field index="8" term="http://rs.tdwg.org/dwc/terms/sampleSizeUnit"/>',
            '<field index="8" term="http://rs.tdwg.org/dwc/terms/scientificName"/>',
        )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("meta.xml", meta)
        archive.writestr("event.txt", event)
        # Intentionally invalid UTF-8. A precheck that opens the response member
        # will fail; a metadata-only precheck must succeed without touching it.
        archive.writestr("occurrence.txt", b"\xff\xfe\x00response-data")
    return path


def test_ecuador_precheck_contract_forbids_occurrence_member_opening():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    auth = value["authorization"]

    assert value["status"] == "FROZEN_METADATA_EVENT_CORE_ONLY_PRECHECK"
    assert auth["archive_container_download_and_hash_authorized"] is True
    assert auth["event_core_rows_read_authorized"] is True
    assert auth["occurrence_extension_member_may_be_opened_or_decompressed"] is False
    assert auth["occurrence_extension_rows_may_be_read"] is False
    assert auth["focal_taxon_response_may_be_opened"] is False
    assert auth["model_fitting_authorized"] is False


def test_precheck_reads_event_core_but_not_invalid_occurrence_member(tmp_path):
    result = precheck(_archive(tmp_path / "candidate.zip"))

    boundary = result["response_boundary"]
    assert boundary["event_core_rows_read"] == 2
    assert boundary["occurrence_extension_files_opened"] is False
    assert boundary["occurrence_extension_rows_read"] == 0
    assert boundary["focal_taxon_response_opened"] is False
    assert result["geometry"]["unique_location_id_or_locality_count"] == 2
    assert result["temporal_support"]["distinct_year_month_count"] == 2
    assert result["effort_and_protocol"]["has_sample_size_value_field"] is True


def test_precheck_fails_before_rows_if_event_core_contains_response_term(tmp_path):
    path = _archive(tmp_path / "bad.zip", response_term_in_core=True)
    try:
        precheck(path)
    except ValueError as exc:
        assert "forbidden response-bearing terms" in str(exc)
    else:
        raise AssertionError("response-bearing Event core must fail closed")


def test_precheck_never_qualifies_candidate_or_opens_response(tmp_path):
    result = precheck(_archive(tmp_path / "candidate.zip"))
    boundary = result["decision_boundary"]

    assert boundary["candidate_qualified"] is False
    assert boundary["focal_response_opening_authorized"] is False
    assert boundary["model_fitting_authorized"] is False
    assert boundary["occurrence_extension_read_authorized"] is False
    assert boundary["separate_followup_contract_required"] is True
