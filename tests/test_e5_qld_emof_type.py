from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_qld_emof_type import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_QLD_EMOF_TYPE_CONTRACT.json"


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
        ignoreHeaderLines="1" rowType="http://rs.iobis.org/obis/terms/ExtendedMeasurementOrFact">
    <files><location>verbatim_extendedmeasurementorfact.txt</location></files>
    <coreid index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/measurementDeterminedBy"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/measurementDeterminedDate"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/measurementID"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/measurementType"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/measurementTypeID"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/measurementValue"/>
  </extension>
</archive>
"""


def _archive(path: Path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("meta.xml", META)
        z.writestr("event.txt", b"must-not-open")
        z.writestr(
            "verbatim_extendedmeasurementorfact.txt",
            "eventID,who,date,measurementID,measurementType,typeID,measurementValue\n"
            "e1,a,b,m1,cameraModel,x,SECRET_MODEL_VALUE\n"
            "e2,a,b,m2,detectionDistance,x,SECRET_DISTANCE_VALUE\n"
            "e3,a,b,m3,speciesCount,x,SECRET_RESPONSE_VALUE\n",
        )
        z.writestr("occurrence.txt", b"\xff\xfe\x00must-not-open")
    return path


def _contract(tmp_path: Path, archive: Path):
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    value["source"]["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    p = tmp_path / "contract.json"
    p.write_text(json.dumps(value), encoding="utf-8")
    return p


def test_contract_is_type_only_and_nonqualifying():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["measurementtype_read_authorized"] is True
    assert fw["measurementvalue_decode_authorized"] is False
    assert fw["measurementvalue_retain_authorized"] is False
    assert fw["measurementvalue_report_authorized"] is False
    assert value["gate_boundary"]["G4_pass_authorized"] is False
    assert value["gate_boundary"]["candidate_qualification_authorized"] is False


def test_emof_precheck_reports_safe_types_but_never_measurement_values(tmp_path):
    archive = _archive(tmp_path / "candidate.zip")
    value = precheck(archive, _contract(tmp_path, archive))

    by_name = {
        row["measurement_type"]: row
        for row in value["measurement_types"]["safe_or_unclassified"]
    }
    assert by_name["cameraModel"]["schema_classification"] == (
        "POTENTIALLY_RESPONSE_INDEPENDENT"
    )
    assert by_name["detectionDistance"]["schema_classification"] == (
        "POTENTIALLY_RESPONSE_INDEPENDENT"
    )
    assert "speciesCount" not in by_name
    assert value["measurement_types"]["masked_potentially_response_bearing_rows"] == 1

    scan = value["scan"]
    assert scan["measurementvalue_values_decoded"] == 0
    assert scan["measurementvalue_values_retained"] == 0
    assert scan["measurementvalue_values_reported"] == 0

    dumped = json.dumps(value)
    assert "SECRET_MODEL_VALUE" not in dumped
    assert "SECRET_DISTANCE_VALUE" not in dumped
    assert "SECRET_RESPONSE_VALUE" not in dumped


def test_emof_precheck_reads_no_biological_extensions(tmp_path):
    archive = _archive(tmp_path / "candidate.zip")
    value = precheck(archive, _contract(tmp_path, archive))
    boundary = value["response_boundary"]
    assert boundary["event_core_rows_read"] == 0
    assert boundary["occurrence_rows_read"] == 0
    assert boundary["verbatim_occurrence_rows_read"] == 0
    assert boundary["multimedia_rows_read"] == 0
    assert boundary["species_or_taxon_values_read"] == 0
    assert boundary["focal_response_opened"] is False
    assert value["decision"]["candidate_qualified"] is False


def test_emof_precheck_never_decodes_measurementvalue_tail_bytes(tmp_path):
    path = tmp_path / "invalid-tail.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("meta.xml", META)
        z.writestr("event.txt", b"must-not-open")
        payload = (
            b"eventID,who,date,measurementID,measurementType,typeID,measurementValue\n"
            b"e1,a,b,m1,cameraModel,x," + bytes([0xff, 0xfe, 0x80]) + b"\n"
        )
        z.writestr("verbatim_extendedmeasurementorfact.txt", payload)
        z.writestr("occurrence.txt", b"\xff\xfe\x00must-not-open")

    value = precheck(path, _contract(tmp_path, path))
    assert value["scan"]["row_count"] == 1
    assert value["scan"]["prefix_parse_failures"] == 0
    assert value["measurement_types"]["safe_or_unclassified"][0][
        "measurement_type"
    ] == "cameraModel"
    assert value["scan"]["measurementvalue_values_decoded"] == 0
