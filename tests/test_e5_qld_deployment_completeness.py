from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_qld_deployment_completeness import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_QLD_DEPLOYMENT_COMPLETENESS_CONTRACT.json"
WORKFLOW = ROOT / ".github" / "workflows" / "e5-qld-deployment-completeness-once.yml"


META = """<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <extension encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1" rowType="http://ala.org.au/terms/1.0/VerbatimEvent">
    <files><location>verbatim_event.txt</location></files>
    <coreid index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/parentEventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/eventType"/>
    <field index="4" term="http://ala.org.au/terms/1.0/deploymentGroups"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/locality"/>
    <field index="8" term="http://rs.tdwg.org/dwc/terms/samplingProtocol"/>
    <field index="9" term="http://rs.tdwg.org/dwc/terms/habitat"/>
    <field index="10" term="http://rs.tdwg.org/dwc/terms/eventRemarks"/>
  </extension>
</archive>
"""


def _archive(path: Path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("meta.xml", META)
        z.writestr(
            "verbatim_event.txt",
            "eventID,parentEventID,eventDate,eventType,deploymentGroups,decimalLatitude,decimalLongitude,locality,samplingProtocol,habitat,eventRemarks\n"
            "d1,s1,2023-01-01/2023-07-31,Deployment,g1,-17.0,145.0,L1,camera trap,rainforest,secret road text\n"
            "d2,s1,,Deployment,g1,-17.1,145.1,L1,camera trap,rainforest,secret bush text\n"
            "d3,s2,2023-02-01/2023-08-31,Deployment,g2,-18.0,146.0,L2,camera trap,rainforest,secret forest text\n"
            "t1,d1,2023-01-05,Trigger,g1,-17.0,145.0,L1,camera trap,rainforest,trigger response text\n"
        )
        z.writestr("event.txt", b"\xff\xfe\x00must-not-open")
        z.writestr("occurrence.txt", b"\xff\xfe\x00must-not-open")
        z.writestr("verbatim_extendedmeasurementorfact.txt", b"\xff\xfe\x00must-not-open")
    return path


def _contract(tmp_path: Path, archive: Path):
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    value["source"]["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    local = tmp_path / "contract.json"
    local.write_text(json.dumps(value), encoding="utf-8")
    return local


def test_contract_is_response_blind_complete_case_only():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["eventremarks_value_decode_authorized"] is False
    assert fw["event_core_rows_read_authorized"] is False
    assert fw["emof_rows_read_authorized"] is False
    assert fw["occurrence_rows_read_authorized"] is False
    assert fw["species_or_taxon_values_authorized"] is False
    assert value["gate_boundary"]["G3_pass_authorized"] is False
    assert value["gate_boundary"]["G4_pass_authorized"] is False
    assert value["gate_boundary"]["candidate_qualification_authorized"] is False


def test_precheck_counts_missing_date_without_decoding_forbidden_tail(tmp_path):
    archive = _archive(tmp_path / "candidate.zip")
    value = precheck(archive, _contract(tmp_path, archive))

    missing = value["missingness"]
    assert missing["deployment_rows"] == 3
    assert missing["missing_eventdate"] == 1
    assert missing["complete_case_rows"] == 2
    assert value["complete_case_geometry"]["unique_coordinate_pairs"] == 2
    assert value["complete_case_geometry"]["unique_localities"] == 2
    assert value["complete_case_geometry"]["distinct_calendar_month_count"] == 8

    boundary = value["response_boundary"]
    assert boundary["eventremarks_values_decoded"] == 0
    assert boundary["event_core_rows_read"] == 0
    assert boundary["emof_rows_read"] == 0
    assert boundary["occurrence_rows_read"] == 0
    assert boundary["species_or_taxon_values_read"] == 0
    assert boundary["raw_eventids_reported"] == 0
    assert boundary["focal_response_opened"] is False


def test_workflow_is_pure_marker_and_pins_contract():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/qld-deployment-completeness-v1" in text
    assert "E5_QLD_DEPLOYMENT_COMPLETENESS_AUTHORIZED.json" in text
    assert "f97cce83c362a8d48d1a48a6b5baee47c345235f" in text
    assert "workflow_dispatch" not in text
    assert "biological_response_opening_authorized" in text
    assert "precheck_e5_qld_deployment_completeness.py" in text
