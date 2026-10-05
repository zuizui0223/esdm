from __future__ import annotations

import json
from pathlib import Path

from scripts.precheck_e5_udzungwa_header import precheck

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_UDZUNGWA_HEADER_CONTRACT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-udzungwa-header-once.yml"

def test_contract_forbids_all_data_rows():
    v=json.loads(CONTRACT.read_text())
    fw=v["response_firewall"]
    assert fw["csv_header_line_read_authorized"] is True
    assert fw["csv_second_line_or_later_read_authorized"] is False
    assert fw["csv_data_rows_read_authorized"] is False
    assert fw["species_response_values_authorized"] is False
    assert fw["focal_response_opening_authorized"] is False

def test_precheck_reads_header_not_poison_second_line(tmp_path):
    p=tmp_path/"candidate.csv"
    p.write_bytes(
        b"title,actual_date_out,retrieval_date,timestamp,camera_id\n"
        b"\xff\xfe\x00POISON_RESPONSE_ROW"
    )
    v=json.loads(CONTRACT.read_text())
    import hashlib
    v["source"]["expected_md5"]=hashlib.md5(p.read_bytes()).hexdigest()
    local=tmp_path/"contract.json"
    local.write_text(json.dumps(v))
    result=precheck(p,local)
    assert result["header"]["columns"] == [
        "title","actual_date_out","retrieval_date","timestamp","camera_id"
    ]
    assert result["response_boundary"]["header_lines_read"] == 1
    assert result["response_boundary"]["data_rows_read"] == 0
    assert result["response_boundary"]["response_rows_read"] == 0

def test_workflow_is_marker_only_and_pins_source():
    text=WORKFLOW.read_text()
    assert "e5/udzungwa-header-v1" in text
    assert "E5_UDZUNGWA_HEADER_AUTHORIZED.json" in text
    assert "42813a1722da2227ec1f4e76cfe52fed8cb4a734" in text
    assert "fb6c9a82c237b8ec3ef80aa8933b8ede" in text or "dat_v3.csv" in text
    assert "workflow_dispatch" not in text
