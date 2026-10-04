from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_qld_survey_parent_effort import precheck


ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_QLD_SURVEY_PARENT_EFFORT_CONTRACT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-qld-survey-parent-effort-once.yml"

META="""<?xml version="1.0" encoding="UTF-8"?>
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
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("meta.xml",META)
        payload=(
            b"eventID,parentEventID,eventDate,eventType,deploymentGroups,decimalLatitude,decimalLongitude,locality,samplingProtocol,habitat,eventRemarks\n"
            b"s1,,2023-01-01/2023-07-31,Survey,g1,,,L1,,,survey secret\n"
            b"s2,,2023-02-01/2023-08-31,Survey,g2,,,L2,,,survey secret\n"
            b"d1,s1,,Deployment,g1,-17.0,145.0,L1,,,deployment secret\n"
            b"d2,s1,,Deployment,g1,-17.1,145.1,L1,,,deployment secret\n"
            b"d3,s2,,Deployment,g2,-18.0,146.0,L2,,,deployment secret\n"
            b"t1,d1," + bytes([0xff,0xfe]) + b",Trigger,g1,-17.0,145.0,L1,camera trap,,trigger secret\n"
        )
        z.writestr("verbatim_event.txt",payload)
        z.writestr("event.txt",b"\xff\xfe\x00must-not-open")
        z.writestr("occurrence.txt",b"\xff\xfe\x00must-not-open")
        z.writestr("verbatim_extendedmeasurementorfact.txt",b"\xff\xfe\x00must-not-open")
    return path

def _contract(tmp_path: Path, archive: Path):
    value=json.loads(CONTRACT.read_text())
    value["source"]["archive_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
    p=tmp_path/"contract.json"
    p.write_text(json.dumps(value))
    return p

def test_contract_forbids_trigger_dates_and_biology():
    value=json.loads(CONTRACT.read_text())
    assert value["inheritance_rule"]["trigger_eventdate_use_authorized"] is False
    assert value["inheritance_rule"]["biological_response_use_authorized"] is False
    fw=value["response_firewall"]
    assert fw["trigger_eventdate_decode_authorized"] is False
    assert fw["eventremarks_value_decode_authorized"] is False
    assert fw["event_core_rows_read_authorized"] is False
    assert fw["emof_rows_read_authorized"] is False
    assert fw["species_or_taxon_values_authorized"] is False

def test_survey_parent_inheritance_uses_no_trigger_dates(tmp_path):
    archive=_archive(tmp_path/"candidate.zip")
    value=precheck(archive,_contract(tmp_path,archive))
    g=value["geometry"]
    assert g["survey_rows"] == 2
    assert g["deployment_rows"] == 3
    assert g["unique_parent_survey_matches"] == 3
    assert g["deployments_with_valid_inherited_interval"] == 3
    assert g["deployment_group_matches"] == 3
    assert g["deployment_group_mismatches"] == 0
    assert g["derived_unique_coordinate_pairs"] == 3
    assert g["derived_unique_localities"] == 2
    assert g["derived_distinct_calendar_month_count"] == 8
    b=value["response_boundary"]
    assert b["trigger_rows_skipped_without_eventdate_decode"] == 1
    assert b["trigger_eventdates_decoded"] == 0
    assert b["eventremarks_values_decoded"] == 0
    assert b["event_core_rows_read"] == 0
    assert b["emof_rows_read"] == 0
    assert b["species_or_taxon_values_read"] == 0
    assert b["focal_response_opened"] is False

def test_workflow_is_pure_marker_and_pins_contract():
    text=WORKFLOW.read_text()
    assert "e5/qld-survey-parent-effort-v1" in text
    assert "E5_QLD_SURVEY_PARENT_EFFORT_AUTHORIZED.json" in text
    assert "a6b9e20a4b832f5e28a2bf270948144cfe621737" in text
    assert "workflow_dispatch" not in text
    assert "trigger_eventdate_use_authorized" in text
    assert "biological_response_opening_authorized" in text
