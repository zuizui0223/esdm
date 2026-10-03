from __future__ import annotations

import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_qld_verbatim_event import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_QLD_VERBATIM_EVENT_CONTRACT.json"
WORKFLOW = ROOT / ".github" / "workflows" / "e5-qld-verbatim-event-once.yml"


META = """<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <core encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Event">
    <files><location>event.txt</location></files>
    <id index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://ala.org.au/terms/1.0/taxonKey"/>
  </core>
  <extension encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1" rowType="http://ala.org.au/terms/1.0/VerbatimEvent">
    <files><location>verbatim_event.txt</location></files>
    <coreid index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/parentEventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/eventType"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/samplingProtocol"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/samplingEffort"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/habitat"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/locality"/>
    <field index="8" term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="9" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
    <field index="10" term="http://ala.org.au/terms/1.0/deploymentGroups"/>
    <field index="11" term="http://rs.tdwg.org/dwc/terms/eventRemarks"/>
    <field index="12" term="http://rs.tdwg.org/dwc/terms/coordinateUncertaintyInMeters"/>
  </extension>
  <extension encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files><location>occurrence.txt</location></files>
    <coreid index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
  </extension>
</archive>
"""


def _archive(path: Path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("meta.xml", META)
        z.writestr("event.txt", b"must-not-open")
        z.writestr(
            "verbatim_event.txt",
            "eventID,parentEventID,eventType,eventDate,samplingProtocol,samplingEffort,"
            "habitat,locality,lat,lon,deploymentGroups,eventRemarks,uncertainty\n"
            "e1,,deployment,2022-01-01/2022-06-30,camera,181 days,road,L1,-17,145,g1,SENSITIVE FREE TEXT,10\n"
            "e2,e1,deployment,2022-01-01/2022-06-30,camera,181 days,bush,L1,-17.001,145.001,g1,OTHER SECRET,10\n"
            "e3,,deployment,2022-07-01/2022-12-31,camera,184 days,road,L2,-18,146,g2,SECRET,10\n"
            "e4,e3,deployment,2022-07-01/2022-12-31,camera,184 days,bush,L2,-18.001,146.001,g2,SECRET,10\n",
        )
        z.writestr("occurrence.txt", b"\xff\xfe\x00species-must-not-open")
        z.writestr("verbatim_occurrence.txt", b"\xff\xfe\x00must-not-open")
    return path


def _local_contract(tmp_path: Path, archive: Path):
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    import hashlib
    value["source"]["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    p = tmp_path / "contract.json"
    p.write_text(json.dumps(value), encoding="utf-8")
    return p


def test_contract_keeps_occurrence_and_free_text_out_of_outputs():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["verbatim_event_rows_read_authorized"] is True
    assert fw["occurrence_extension_data_read_authorized"] is False
    assert fw["verbatim_occurrence_rows_read_authorized"] is False
    assert fw["eventremarks_values_may_be_retained"] is False
    assert fw["eventremarks_values_may_be_reported"] is False
    assert value["decision_boundary"]["G4_pass_authorized"] is False


def test_verbatim_event_geometry_is_summarized_without_response_values(tmp_path):
    archive = _archive(tmp_path / "candidate.zip")
    value = precheck(archive, _local_contract(tmp_path, archive))

    assert value["geometry"]["row_count"] == 4
    assert value["geometry"]["unique_event_ids"] == 4
    assert value["geometry"]["unique_coordinate_pairs"] == 4
    assert value["geometry"]["distinct_calendar_month_count"] == 12
    assert value["categories"]["habitat"]["values"] == {"bush": 2, "road": 2}

    groups = value["deployment_group_geometry"]
    assert groups["unique_nonempty_groups"] == 2
    assert groups["groups_with_multiple_rows"] == 2
    assert groups["groups_with_multiple_habitat_values"] == 2
    assert groups["raw_group_values_reported"] is False

    dumped = json.dumps(value)
    assert "SENSITIVE FREE TEXT" not in dumped
    assert "OTHER SECRET" not in dumped

    boundary = value["response_boundary"]
    assert boundary["event_core_rows_read"] == 0
    assert boundary["eventremarks_values_retained"] == 0
    assert boundary["eventremarks_values_reported"] == 0
    assert boundary["occurrence_rows_read"] == 0
    assert boundary["verbatim_occurrence_rows_read"] == 0
    assert boundary["species_or_taxon_values_read"] == 0
    assert boundary["focal_response_opened"] is False


def test_workflow_is_pure_marker_and_pins_archive_identity():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/qld-verbatim-event-v1" in text
    assert "E5_QLD_VERBATIM_EVENT_AUTHORIZED.json" in text
    assert "fad0fd87700e5276fceea0a726619f1444c3fd37" in text
    assert "f830085a5c1ad6ec9e130169188049670ffa83372a08a02924aa6190554de34e" in text
    assert "workflow_dispatch" not in text
    assert "occurrence_opening_authorized" in text
    assert "precheck_e5_qld_verbatim_event.py" in text
