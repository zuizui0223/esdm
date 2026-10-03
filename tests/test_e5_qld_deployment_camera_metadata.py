from __future__ import annotations
import hashlib
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_qld_deployment_camera_metadata import precheck

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_QLD_DEPLOYMENT_CAMERA_METADATA_CONTRACT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-qld-deployment-camera-metadata-once.yml"

META="""<?xml version="1.0" encoding="UTF-8"?>
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
  <extension encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1" rowType="http://rs.iobis.org/obis/terms/ExtendedMeasurementOrFact">
    <files><location>verbatim_extendedmeasurementorfact.txt</location></files>
    <coreid index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/measurementID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/measurementType"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/measurementTypeID"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/measurementValue"/>
  </extension>
</archive>
"""

def _archive(path: Path):
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("meta.xml",META)
        z.writestr("event.txt",b"must-not-open")
        z.writestr(
            "verbatim_event.txt",
            "eventID,parentEventID,eventDate,eventType,deploymentGroups,decimalLatitude,decimalLongitude,locality,samplingProtocol,habitat,eventRemarks\n"
            "d1,s1,2023-01-01/2023-02-28,Deployment,g1,0.0,0.0,L1,camera trap,rainforest,road camera\n"
            "d2,s1,2023-01-01/2023-02-28,Deployment,g1,0.00045,0.0,L1,camera trap,rainforest,bush camera\n"
            "t1,d1,2023-01-10,Trigger,g1,0.0,0.0,L1,camera trap,rainforest,trigger\n"
        )
        lines=["coreid,measurementID,measurementType,typeID,x,y,measurementValue"]
        for core,camera in [("d1","camA"),("d2","camB")]:
            for typ,val in [
                ("cameraID",camera),("cameraModel","ModelX"),("cameraDelay","1"),
                ("cameraHeight","50"),("cameraTilt","0")
            ]:
                lines.append(f"{core},m,{typ},x,x,x,{val}")
        payload=("\n".join(lines)+"\n").encode()
        payload += b"d1,m,speciesCount,x,x,x," + bytes([0xff,0xfe,0x80]) + b"\n"
        z.writestr("verbatim_extendedmeasurementorfact.txt",payload)
        z.writestr("occurrence.txt",b"\xff\xfe\x00must-not-open")
    return path

def _contract(tmp_path: Path, archive: Path):
    value=json.loads(CONTRACT.read_text())
    value["source"]["archive_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
    p=tmp_path/"contract.json"
    p.write_text(json.dumps(value))
    return p

def test_contract_freezes_allowlist_and_keeps_biology_closed():
    v=json.loads(CONTRACT.read_text())
    assert v["emof_value_allowlist"] == ["cameraID","cameraModel","cameraDelay","cameraHeight","cameraTilt"]
    fw=v["response_firewall"]
    assert fw["emof_allowlisted_measurementvalue_decode_authorized"] is True
    assert fw["emof_nonallowlisted_measurementvalue_decode_authorized"] is False
    assert fw["occurrence_rows_read_authorized"] is False
    assert fw["species_or_taxon_values_authorized"] is False
    assert fw["focal_response_opening_authorized"] is False
    assert v["gate_boundary"]["candidate_qualification_authorized"] is False

def test_precheck_joins_safe_camera_metadata_and_never_decodes_nonallowlisted_tail(tmp_path):
    archive=_archive(tmp_path/"candidate.zip")
    value=precheck(archive,_contract(tmp_path,archive))
    assert value["geometry"]["deployment_rows"] == 2
    assert value["geometry"]["unique_coordinate_pairs"] == 2
    assert value["camera_metadata"]["distinct_camera_id_count"] == 2
    assert value["camera_metadata"]["raw_camera_ids_reported"] == 0
    assert value["camera_metadata"]["emof_scan"]["nonallowlisted_measurementvalue_values_decoded"] == 0
    for typ in ["cameraID","cameraModel","cameraDelay","cameraHeight","cameraTilt"]:
        assert value["camera_metadata"]["completeness"][typ]["exactly_one"] == 2
        assert value["camera_metadata"]["completeness"][typ]["missing"] == 0
    assert value["placement_and_pairing"]["placement_class_counts"] == {
        "BUSH":1,"ROAD_TRAIL":1
    }
    assert value["placement_and_pairing"]["matched_road_bush_pair_count"] == 1
    assert value["response_boundary"]["species_or_taxon_values_read"] == 0
    assert value["response_boundary"]["focal_response_opened"] is False

def test_workflow_is_pure_marker_and_pins_contract():
    text=WORKFLOW.read_text()
    assert "e5/qld-deployment-camera-metadata-v1" in text
    assert "E5_QLD_DEPLOYMENT_CAMERA_METADATA_AUTHORIZED.json" in text
    assert "a48a35320d3741231e2c33c91085de515e3ea402" in text
    assert "f830085a5c1ad6ec9e130169188049670ffa83372a08a02924aa6190554de34e" in text
    assert "workflow_dispatch" not in text
    assert "biological_response_opening_authorized" in text
