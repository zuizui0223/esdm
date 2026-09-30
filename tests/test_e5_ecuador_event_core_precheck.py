from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from scripts.precheck_e5_ecuador_event_core import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication"
    / "E5_ECUADOR_EVENT_CORE_PRECHECK_CONTRACT.json"
)


def _meta(*, sensitive_core=False):
    extra_core = (
        '<field index="8" term="http://rs.tdwg.org/dwc/terms/scientificName"/>'
        if sensitive_core else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <core encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n"
        fieldsEnclosedBy="&quot;" ignoreHeaderLines="1"
        rowType="http://rs.tdwg.org/dwc/terms/Event">
    <files><location>event.txt</location></files>
    <id index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/locationID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/samplingProtocol"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/samplingEffort"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/parentEventID"/>
    {extra_core}
  </core>
  <extension encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n"
             fieldsEnclosedBy="&quot;" ignoreHeaderLines="1"
             rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files><location>occurrence.txt</location></files>
    <coreid index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/occurrenceID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
  </extension>
</archive>
"""


def _archive(tmp_path: Path, *, sensitive_core=False) -> Path:
    path = tmp_path / "ecuador.zip"
    header = [
        "eventID", "locationID", "eventDate", "samplingProtocol",
        "samplingEffort", "decimalLatitude", "decimalLongitude",
        "parentEventID",
    ]
    if sensitive_core:
        header.append("scientificName")
    rows = ["\t".join(header)]
    for i in range(958):
        location = f"loc-{i % 40:02d}"
        month = 1 + (i % 12)
        values = [
            f"event-{i:04d}",
            location,
            f"2023-{month:02d}-01/2023-{month:02d}-14",
            "camera trap",
            "14 days",
            f"{-4.0 + (i % 40) * 0.01:.3f}",
            f"{-79.0 + (i % 40) * 0.01:.3f}",
            f"landscape-{i % 4}",
        ]
        if sensitive_core:
            values.append("SHOULD_NOT_BE_READ")
        rows.append("\t".join(values))

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("meta.xml", _meta(sensitive_core=sensitive_core))
        archive.writestr("event.txt", "\n".join(rows) + "\n")
        # Deliberately invalid UTF-8: the precheck must succeed without opening it.
        archive.writestr("occurrence.txt", b"\xff\xfe\x00BIOLOGICAL-RESPONSE")
        archive.writestr("eml.xml", "<eml>metadata only</eml>")
    return path


def test_contract_forbids_occurrence_data_and_outcome_opening():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    firewall = value["response_firewall"]
    assert value["status"] == "FROZEN_PRECHECK_NOT_AUTHORIZED"
    assert firewall["event_core_read_authorized"] is True
    assert firewall["occurrence_extension_data_read_authorized"] is False
    assert firewall["expected_occurrence_rows_read"] == 0
    assert firewall["archive_may_not_be_uploaded_as_artifact"] is True
    assert value["boundary"]["candidate_qualification_authorized"] is False
    assert value["boundary"]["focal_response_opening_authorized"] is False
    assert value["boundary"]["model_fitting_authorized"] is False


def test_event_core_precheck_never_opens_invalid_occurrence_file(tmp_path):
    result = precheck(_archive(tmp_path), CONTRACT)

    boundary = result["response_boundary"]
    assert result["status"] == "E5_RESPONSE_BLIND_EVENT_CORE_PRECHECK"
    assert boundary["event_core_opened"] is True
    assert boundary["occurrence_extension_opened"] is False
    assert boundary["occurrence_rows_read"] == 0
    assert boundary["archive_uploaded_as_artifact"] is False
    assert result["archive"]["event_core_row_count"] == 958
    assert result["archive"]["occurrence_extension_declared"] is True


def test_precheck_reports_only_potential_design_support(tmp_path):
    result = precheck(_archive(tmp_path), CONTRACT)
    geometry = result["event_core_geometry"]
    hints = result["preliminary_gate_hints"]

    assert geometry["physical_location_candidate_count"] == 40
    assert geometry["locations_with_two_or_more_event_rows"] == 40
    assert geometry["distinct_calendar_months"] == 12
    assert geometry["event_date_parseable_rows"] == 958

    assert hints["G1_INDEPENDENT_SOURCE"] == "PASS_FROM_PARENT_REGISTRY"
    assert hints["G2_SCHEMA_EFFORT_TIME"].startswith("PARTIAL_")
    assert hints["G3_CROSSED_DOMAIN"] == "MANUAL_REVIEW_REQUIRED"
    assert hints["G4_DETECTION_IDENTIFIABILITY"].startswith("POTENTIAL_")
    assert hints["G5_PHYSICAL_REPLICATION"].startswith("POTENTIAL_")
    assert hints["G6_TEMPORAL_SUPPORT"].startswith("POTENTIAL_")
    assert hints["G7_MODEL_FREEZE"] == "NOT_REACHED"

    assert result["decision"]["candidate_qualified"] is False
    assert result["decision"]["focal_response_opening_authorized"] is False
    assert result["decision"]["model_fitting_authorized"] is False


def test_precheck_can_inspect_occurrence_schema_without_occurrence_values(tmp_path):
    result = precheck(_archive(tmp_path), CONTRACT)
    schema = result["occurrence_extension_schema_from_meta_xml_only"]

    assert schema["taxon_identity_declared"] is True
    assert schema["event_link_declared"] is True
    assert schema["event_time_term_declared"] is True
    assert schema["occurrence_id_declared"] is True
    assert schema["values_opened"] is False


def test_precheck_refuses_event_core_that_contains_taxonomic_response(tmp_path):
    with pytest.raises(ValueError, match="response-bearing/taxonomic"):
        precheck(_archive(tmp_path, sensitive_core=True), CONTRACT)
