from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_QLD_DEPLOYMENT_CAMERA_METADATA_CONTRACT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-qld-deployment-camera-metadata-once.yml"

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

def test_workflow_is_pure_marker_and_pins_contract():
    text=WORKFLOW.read_text()
    assert "e5/qld-deployment-camera-metadata-v1" in text
    assert "E5_QLD_DEPLOYMENT_CAMERA_METADATA_AUTHORIZED.json" in text
    assert "a48a35320d3741231e2c33c91085de515e3ea402" in text
    assert "f830085a5c1ad6ec9e130169188049670ffa83372a08a02924aa6190554de34e" in text
    assert "workflow_dispatch" not in text
    assert "biological_response_opening_authorized" in text
