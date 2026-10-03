from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_qld_emof_types import precheck

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_QLD_EMOF_TYPES_CONTRACT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-qld-emof-types-once.yml"

META="""<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <extension encoding="UTF-8" fieldsTerminatedBy="," fieldsEnclosedBy="&quot;"
        ignoreHeaderLines="1"
        rowType="http://rs.iobis.org/obis/terms/ExtendedMeasurementOrFact">
    <files><location>verbatim_extendedmeasurementorfact.txt</location></files>
    <coreid index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.iobis.org/obis/terms/measurementID"/>
    <field index="2" term="http://rs.iobis.org/obis/terms/measurementType"/>
    <field index="3" term="http://rs.iobis.org/obis/terms/measurementTypeID"/>
    <field index="4" term="http://rs.iobis.org/obis/terms/measurementValue"/>
    <field index="5" term="http://rs.iobis.org/obis/terms/measurementDeterminedBy"/>
    <field index="6" term="http://rs.iobis.org/obis/terms/measurementDeterminedDate"/>
  </extension>
</archive>
"""

def _archive(path: Path):
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("meta.xml", META)
        z.writestr(
            "verbatim_extendedmeasurementorfact.txt",
            "eventID,measurementID,measurementType,measurementTypeID,measurementValue,by,date\n"
            "e1,m1,cameraModel,urn:camera,SECRET_MODEL,A,2022-01-01\n"
            "e1,m2,featureType,urn:feature,roadDirt,B,2022-01-01\n"
            "e2,m3,detectionDistance,urn:distance,25,C,2022-01-01\n"
            "e3,m4,speciesCount,urn:response,MUST_NOT_READ,D,2022-01-01\n"
        )
        z.writestr("occurrence.txt", b"\xff\xfe\x00must-not-open")
    return path

def _contract(tmp_path: Path, archive: Path):
    value=json.loads(CONTRACT.read_text(encoding="utf-8"))
    value["source"]["archive_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
    p=tmp_path/"contract.json"
    p.write_text(json.dumps(value),encoding="utf-8")
    return p

def test_contract_forbids_measurement_values_and_occurrences():
    value=json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw=value["response_firewall"]
    assert fw["emof_rows_read_authorized"] is True
    assert fw["measurement_value_values_may_be_retained"] is False
    assert fw["measurement_value_values_may_be_reported"] is False
    assert fw["occurrence_extension_data_read_authorized"] is False
    assert value["decision_boundary"]["G3_pass_authorized"] is False
    assert value["decision_boundary"]["G4_pass_authorized"] is False

def test_type_precheck_reads_type_names_but_never_measurement_values(tmp_path):
    archive=_archive(tmp_path/"candidate.zip")
    value=precheck(archive,_contract(tmp_path,archive))
    assert value["geometry"]["row_count"] == 4
    names={r["measurement_type"]:r for r in value["measurement_types"]}
    assert names["cameraModel"]["classification"] == "POTENTIAL_SOURCE_PROTOCOL_METADATA"
    assert names["featureType"]["classification"] == "POTENTIAL_SOURCE_PROTOCOL_METADATA"
    assert names["detectionDistance"]["classification"] == "POTENTIAL_DETECTION_METADATA"
    assert names["speciesCount"]["classification"] == "RESPONSE_LIKE_TYPE_VALUE_REMAINS_FORBIDDEN"
    dumped=json.dumps(value)
    assert "SECRET_MODEL" not in dumped
    assert "roadDirt" not in dumped
    assert "MUST_NOT_READ" not in dumped
    b=value["response_boundary"]
    assert b["measurement_values_read"] == 0
    assert b["occurrence_rows_read"] == 0
    assert b["species_or_taxon_values_read"] == 0

def test_workflow_is_pure_marker_and_measurement_values_closed():
    text=WORKFLOW.read_text(encoding="utf-8")
    assert "e5/qld-emof-types-v1" in text
    assert "E5_QLD_EMOF_TYPES_AUTHORIZED.json" in text
    assert "7fc7be539a0435a5771f1193478e884afaac0a4e" in text
    assert "workflow_dispatch" not in text
    assert "measurement_value_opening_authorized" in text
    assert "occurrence_opening_authorized" in text
