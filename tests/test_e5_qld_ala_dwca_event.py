from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_qld_ala_dwca_event import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_QLD_ALA_DWCA_EVENT_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-qld-ala-dwca-event-once.yml"
)


META = """<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <core encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1"
        rowType="http://rs.tdwg.org/dwc/terms/Event">
    <files><location>event.csv</location></files>
    <id index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/parentEventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/locationID"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/samplingProtocol"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
  </core>
  <extension encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1"
        rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files><location>occurrence.csv</location></files>
    <coreid index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
  </extension>
</archive>
"""


def _archive(path: Path, *, response_bearing_core=False):
    meta = META
    if response_bearing_core:
        meta = meta.replace(
            '<field index="6" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>',
            '<field index="6" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>'
            '<field index="7" term="http://rs.tdwg.org/dwc/terms/scientificName"/>',
        )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("meta.xml", meta)
        if response_bearing_core:
            z.writestr(
                "event.csv",
                "eventID,parentEventID,locationID,eventDate,samplingProtocol,lat,lon,scientificName\n"
                "e1,,l1,2022-01-01/2022-06-30,camera,-17,145,SENSITIVE\n",
            )
        else:
            z.writestr(
                "event.csv",
                "eventID,parentEventID,locationID,eventDate,samplingProtocol,lat,lon\n"
                "e1,,l1,2022-01-01/2022-06-30,camera,-17,145\n"
                "e2,e1,l1,2022-07-01,camera,-17,145\n",
            )
        # Must never be opened.
        z.writestr("occurrence.csv", b"\xff\xfe\x00species-response-must-not-open")
    return path


def test_contract_keeps_occurrence_extension_and_taxon_values_closed():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["event_core_response_independent_rows_read_authorized"] is True
    assert fw["occurrence_extension_data_read_authorized"] is False
    assert fw["species_or_taxon_value_read_authorized"] is False
    assert fw["expected_occurrence_rows_read"] == 0
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False


def test_safe_event_core_can_be_summarized_without_occurrence_rows(tmp_path):
    value = precheck(_archive(tmp_path / "safe.zip"), CONTRACT)

    assert value["status"] == "E5_RESPONSE_BLIND_QLD_EVENT_CORE_PRECHECK"
    summary = value["event_core_summary"]
    assert summary["status"] == "SAFE_EVENT_CORE_READ"
    assert summary["rows_read"] == 2
    assert summary["unique_event_ids"] == 2
    assert summary["unique_location_ids"] == 1
    assert summary["distinct_calendar_month_count"] == 7

    boundary = value["response_boundary"]
    assert boundary["occurrence_extension_data_opened"] is False
    assert boundary["occurrence_rows_read"] == 0
    assert boundary["species_or_taxon_values_read"] == 0
    assert boundary["focal_response_opened"] is False


def test_response_bearing_event_core_fails_before_any_core_row_is_read(tmp_path):
    value = precheck(
        _archive(tmp_path / "blocked.zip", response_bearing_core=True),
        CONTRACT,
    )
    assert value["status"] == "E5_RESPONSE_BLIND_QLD_EVENT_CORE_SCHEMA_STOP"
    assert value["event_core_summary"]["status"] == "SCHEMA_STOP_RESPONSE_BEARING_CORE"
    assert value["event_core_summary"]["rows_read"] == 0
    assert "scientificname" in value["event_core_summary"]["forbidden_declared_terms"]
    assert value["response_boundary"]["occurrence_rows_read"] == 0


def test_workflow_is_pure_marker_and_occurrence_closed():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/qld-ala-dwca-event-v1" in text
    assert "E5_QLD_ALA_DWCA_EVENT_AUTHORIZED.json" in text
    assert "f654e244f73bf7970d9af5f1f416d9259d21aac1" in text
    assert "dwca-exports.ala.org.au/dr31594.zip" in text
    assert "workflow_dispatch" not in text
    assert "occurrence_extension_opening_authorized" in text
    assert "precheck_e5_qld_ala_dwca_event.py" in text
