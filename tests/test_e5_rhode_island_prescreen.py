from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from scripts.precheck_e5_rhode_island_zip_headers import (
    inspect,
    inspect_verified_archive,
    read_csv_first_header,
    schema_flags,
)

ROOT=Path(__file__).resolve().parents[1]
SCREEN=ROOT/"docs"/"replication"/"E5_CANDIDATE_RHODE_ISLAND_PAIRED_CAMERAS_SCREEN.json"
CONTRACT=ROOT/"docs"/"replication"/"E5_RHODE_ISLAND_ZIP_HEADER_CONTRACT.json"
REGISTRY=ROOT/"docs"/"replication"/"E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-rhode-island-zip-headers-once.yml"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fake_zip(*, include_detection=True) -> bytes:
    out=io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "DataS1/RI_CameraSurvey_Deployments.csv",
            "SiteID,CameraID,StartDateTime,EndDateTime,Latitude,Longitude,YearSeason\n"
            "station1,cam001,2020-01-01,2020-01-31,41.0,-71.0,winter2020\n",
        )
        if include_detection:
            archive.writestr(
                "DataS1/RI_CameraSurvey_Detections.csv",
                "SiteID,CameraID,DateTime,Species,YearSeason\n"
                "station1,cam001,2020-01-01 18:00,SECRET_SPECIES,2020winter\n",
            )
        archive.writestr("DataS1/README.txt", "no outcome data should be read")
    return out.getvalue()


def test_frozen_screen_only_nominates_paired_candidate():
    v=_read(SCREEN)
    gates={r["gate"]:r["status"] for r in v["gates"]}
    assert v["candidate_id"]=="rhode_island_paired_cameras_2018_2023"
    assert gates["G4_DETECTION_IDENTIFIABILITY"].startswith(
        "PROMISING_REPLICATE_CAMERA_IDENTITIES"
    )
    assert gates["G3_CROSSED_DOMAIN"].startswith("POTENTIAL_PAIRED")
    assert v["decision"]["candidate_qualified"] is False
    assert v["decision"]["focal_response_opening_authorized"] is False
    assert v["response_boundary"]["biological_rows_read"]==0


def test_frozen_zip_contract_acknowledges_transfer_of_response_containing_archive():
    v=_read(CONTRACT)
    fw=v["response_firewall"]
    assert v["status"]=="FROZEN_ZIP_MEMBER_HEADER_PRECHECK_NOT_AUTHORIZED"
    assert v["source"]["archive_bytes"]==12059878
    assert v["source"]["archive_public_md5"]=="c66943e6c2a9aab0abce2a1eba8ce02e"
    assert fw["whole_archive_bytes_transferred"] is True
    assert fw["archive_may_contain_biological_response_rows"] is True
    assert fw["decode_only_first_CSV_header_line_of_2_pinned_members"] is True
    assert fw["inspect_CSV_data_rows_authorized"] is False
    assert fw["inspect_species_values_authorized"] is False
    assert fw["model_fitting_authorized"] is False
    assert v["decision_boundary"]["G3_pass_authorized"] is False
    assert v["decision_boundary"]["G4_pass_authorized"] is False


def test_header_flags_recognize_distinct_site_camera_effort_event_and_taxon():
    deployment=schema_flags(
        "deployment",
        ["SiteID","CameraID","StartDateTime","EndDateTime","Latitude","Longitude","YearSeason"],
    )
    detection=schema_flags(
        "detection",
        ["SiteID","CameraID","DateTime","Species","YearSeason"],
    )
    assert all(deployment.values())
    assert all(detection.values())


def test_synthetic_zip_only_decodes_headers_not_secret_biological_rows():
    blob=_fake_zip()
    out=inspect_verified_archive(blob,_read(CONTRACT),hashlib.md5(blob).hexdigest())
    assert out["status"]=="RESPONSE_BLIND_HEADER_ROUTE_PLAUSIBLE_UNQUALIFIED"
    assert out["decision"]["nominate_separate_deployment_geometry_child"] is True
    assert out["decision"]["candidate_qualified"] is False
    assert out["decision"]["G4_pass_authorized"] is False
    assert out["response_boundary"]["decoded_biological_data_rows"]==0
    assert out["response_boundary"]["CSVs_whose_first_header_decoded"]==2
    assert "SECRET_SPECIES" not in json.dumps(out)
    assert out["members"]["deployment"]["schema_flags"]["camera_id_named"] is True
    assert out["members"]["detection"]["schema_flags"]["camera_id_named"] is True


def test_absent_detection_member_stops_before_biological_values():
    blob=_fake_zip(include_detection=False)
    out=inspect_verified_archive(blob,_read(CONTRACT),hashlib.md5(blob).hexdigest())
    assert out["status"]=="STOP_OR_HOLD_HEADER_SCHEMA_INCOMPLETE"
    assert out["decision"]["nominate_separate_deployment_geometry_child"] is False
    assert out["response_boundary"]["CSVs_whose_first_header_decoded"]==1
    assert out["decision"]["focal_response_opening_authorized"] is False


def test_unpinned_archive_fails_before_any_member_decoding():
    v=_read(CONTRACT)
    with pytest.raises(ValueError,match="archive byte count"):
        inspect(v,fetcher=lambda url, expected: _fake_zip())


def test_first_header_reader_rejects_unterminated_overlong_headers():
    blob=io.BytesIO()
    with zipfile.ZipFile(blob,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("t.csv","field_one,field_two"+("x"*50))
    with zipfile.ZipFile(io.BytesIO(blob.getvalue())) as z:
        with pytest.raises(ValueError,match="header exceeds"):
            read_csv_first_header(z,z.getinfo("t.csv"),16)


def test_registry_17_unqualified_and_rhode_strongest_named():
    v=_read(REGISTRY)
    row=next(x for x in v["candidates"] if x["candidate_id"]=="rhode_island_paired_cameras_2018_2023")
    assert v["current_conclusion"]["screened_candidate_count"]==17
    assert v["current_conclusion"]["qualified_candidate_count"]==0
    assert v["current_conclusion"]["strongest_current_named_candidate"]=="kays41_emammal_team_2020"
    assert row["decision"]=="E5_CANDIDATE_NOT_QUALIFIED_AT_G4_CURRENT_PUBLIC_PAIR_DESIGN"
    assert row["response_opened"] is False
    assert row["response_may_be_opened_for_E5"] is False


def test_execution_workflow_marker_only_and_pins_contract_blob():
    text=WORKFLOW.read_text(encoding="utf-8")
    assert "e5/rhode-island-paired-camera-zip-headers-once-v1" in text
    assert "E5_RHODE_ISLAND_ZIP_HEADERS_AUTHORIZED.json" in text
    assert "47e26e6e01d5763f055a634ce00bc4c89e8b57f4" in text
    assert "workflow_dispatch" not in text
    assert "authorization commit must change only marker" in text
