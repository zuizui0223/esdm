from __future__ import annotations

import csv
from io import StringIO
import json
from pathlib import Path

import pytest

from scripts.precheck_e5_rhode_island_deployment_geometry import (
    audit_deployment_csv, calendar_months, parse_date,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_RHODE_ISLAND_GEOMETRY_CONTRACT.json"
HEADER=ROOT/"docs"/"replication"/"E5_RHODE_ISLAND_ZIP_HEADER_RECEIPT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-rhode-island-geometry-once.yml"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def make_csv(n_sites: int = 40, disjoint: bool = False) -> bytes:
    out=StringIO()
    writer=csv.writer(out)
    writer.writerow(_contract()["source"]["allowed_member_fields"])
    for i in range(n_sites):
        site=f"SECRET_SITE_{i:03d}"
        latitude=41.45 + (i%3)*0.001
        longitude=-71.85 + i*0.015
        for member in range(2):
            start="2020-01-01" if member==0 or not disjoint else "2020-08-01"
            end="2020-07-31" if member==0 else "2020-10-30"
            writer.writerow([
                "2020_trial",site,f"SECRET_STATION_{i}_{member}",
                f"SECRET_CAM_{i}_{member}",start,end,latitude,
                longitude+(0.0002*member)
            ])
    return out.getvalue().encode("utf-8")


def test_positive_synthetic_geometry_is_only_provisional_not_G4():
    result=audit_deployment_csv(make_csv(),_contract())
    assert result["status"]=="DEPLOYMENT_GEOMETRY_SUPPORTS_NEXT_G4_STRUCTURAL_REVIEW"
    assert result["deployment_summary"]["valid_effort_rows"]==80
    assert result["deployment_summary"]["physical_site_ids_with_consistent_coordinates"]==40
    for block in ("WEST_OPERATIONAL","EAST_OPERATIONAL"):
        b=result["geographic_operational_blocks"][block]
        assert b["independent_physical_sites_with_valid_effort"]==20
        assert b["site_periods_with_matched_camera_overlap"]==20
        assert b["distinct_calendar_months_of_deployment_exposure"]>=6
    assert result["decision"]["operational_split_physical_replication_minima_met"] is True
    assert result["decision"]["operational_split_six_calendar_months_met"] is True
    assert result["decision"]["G4_effective_detection_pass_authorized"] is False
    assert result["decision"]["candidate_qualified"] is False
    assert "SECRET_SITE_000" not in json.dumps(result)
    assert "SECRET_CAM_000_0" not in json.dumps(result)


def test_nonoverlapping_member_deployments_do_not_count_as_calibration():
    result=audit_deployment_csv(make_csv(disjoint=True),_contract())
    assert result["status"]=="DEPLOYMENT_GEOMETRY_INCOMPLETE_OR_QC_HOLD"
    assert result["decision"]["within_site_paired_member_operational_overlap_in_both_blocks"] is False
    for block in ("WEST_OPERATIONAL","EAST_OPERATIONAL"):
        assert result["geographic_operational_blocks"][block][
            "site_periods_with_matched_camera_overlap"
        ]==0
    assert result["decision"]["G4_effective_detection_pass_authorized"] is False


def test_calendar_months_and_declared_date_formats():
    from datetime import date
    assert calendar_months(date(2019,12,20),date(2020,2,3))=={12,1,2}
    assert parse_date("12/20/2019",_contract()["grouping"]["accepted_date_formats"])==date(2019,12,20)
    assert parse_date("wrong",_contract()["grouping"]["accepted_date_formats"]) is None


def test_unexpected_columns_rejected_before_any_geometry():
    bad=make_csv().decode("utf-8").replace("Camera.Name","Species",1)
    with pytest.raises(ValueError,match="unexpected deployment table fields"):
        audit_deployment_csv(bad.encode("utf-8"),_contract())


def test_contract_explicitly_opens_only_deployment_metadata_not_detection():
    v=_contract()
    assert v["status"]=="FROZEN_METADATA_ONLY_GEOMETRY_NOT_AUTHORIZED"
    assert v["source"]["allowed_member"]=="RI_CameraSurvey_Deployments.csv"
    assert v["source"]["forbidden_member"]=="RI_CameraSurvey_Detections.csv"
    assert v["scope"]["open_only_deployment_member"] is True
    assert v["scope"]["full_archive_transfer_containing_biological_rows"] is True
    assert v["scope"]["detection_CSV_stream_open_authorized"] is False
    assert v["scope"]["biological_outcomes_open_authorized"] is False
    assert v["decision_boundary"]["G4_effective_detection_pass_authorized"] is False
    assert v["decision_boundary"]["candidate_qualification_authorized"] is False


def test_header_receipt_is_complete_and_biological_rows_stayed_closed():
    h=json.loads(HEADER.read_text(encoding="utf-8"))
    assert h["execution"]["run_id"]==37747242192
    assert h["execution"]["artifact_id"]==11536362715
    assert h["execution"]["result_json_sha256"]=="e10410b0f98e8781b00fa1eb0c16cfa14b7e656b90bfdf3f2c2df428b85c947b"
    assert h["response_boundary"]["detection_rows_decoded"]==0
    assert h["decision"]["nominate_separate_metadata_only_deployment_geometry_child"] is True


def test_geometry_workflow_pin_and_one_shot_pure_marker():
    text=WORKFLOW.read_text(encoding="utf-8")
    assert "e5/rhode-island-metadata-geometry-once-v1" in text
    assert "E5_RHODE_ISLAND_GEOMETRY_AUTHORIZED.json" in text
    assert "387e1f17d5dd93f213d1b8ddb5ae8ac197b9657c" in text
    assert "workflow_dispatch" not in text
    assert "authorization commit must change only marker" in text
