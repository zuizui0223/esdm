from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from esdm.validate.empirical_snapshot_usa import _stream_bucket
from esdm.validate.empirical_snapshot_usa_transport_v3 import (
    run_snapshot_usa_transport_v3,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_USA_2024_TRANSPORT_V3_CONTRACT.json"


def _deployment_id_for_bucket(target: int, offset: int) -> str:
    index = offset
    while True:
        value = f"dep-{target}-{index:05d}"
        bucket = _stream_bucket(value)
        if (
            target == 0 and bucket <= 63
            or target == 1 and 64 <= bucket <= 127
            or target == 2 and 128 <= bucket <= 207
            or target == 3 and 208 <= bucket <= 255
        ):
            return value
        index += 1


def _deployment_csv() -> bytes:
    fieldnames = [
        "Project",
        "State",
        "Camera_Trap_Array",
        "Site_Name",
        "Deployment_ID",
        "Start_Date",
        "End_Date",
        "Survey_Nights",
        "Latitude",
        "Longitude",
    ]
    rows = []
    for index in range(64):
        rows.append(
            {
                "Project": "fixture",
                "State": "XX",
                "Camera_Trap_Array": f"array-{index // 8:02d}",
                "Site_Name": f"site-{index:03d}",
                "Deployment_ID": _deployment_id_for_bucket(
                    index % 4, index * 100
                ),
                "Start_Date": "2024-09-01",
                "End_Date": "2024-10-31",
                "Survey_Nights": "61",
                "Latitude": str(30.0 + 0.05 * index),
                "Longitude": str(-104.0 + 0.25 * index),
            }
        )
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _sequence_header() -> bytes:
    return (
        "Project,Camera_Trap_Array,Deployment_ID,Sequence_ID,Start_Time,End_Time,"
        "Class,Order,Family,Genus,Species,Common_Name,Age,Sex,Group_Size,"
        "Individual_Animal_Notes,Behavior\n"
    ).encode("utf-8")


class _Response:
    def __init__(self, *, status: int, body: bytes, headers=None):
        self._status = status
        self._body = body
        self.headers = dict(headers or {})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self._status

    def read(self, size=-1):
        return self._body if size is None or size < 0 else self._body[:size]

    def readline(self, size=-1):
        line = self._body.splitlines(keepends=True)[0]
        return line if size is None or size < 0 else line[:size]


class _Opener:
    def __init__(self, *, deployment_status=200, sequence_status=206, content_range="bytes 0-4095/999999"):
        self.deployment_status = deployment_status
        self.sequence_status = sequence_status
        self.content_range = content_range
        self.requests = []

    def open(self, request, timeout=90):
        self.requests.append(request)
        url = request.full_url
        if url.endswith("/api/v2/files/4788613/download"):
            return _Response(
                status=self.deployment_status,
                body=_deployment_csv(),
                headers={"Content-Type": "text/csv"},
            )
        if url.endswith("/api/v2/files/4788614/download"):
            return _Response(
                status=self.sequence_status,
                body=_sequence_header(),
                headers={
                    "Content-Type": "text/csv",
                    **(
                        {"Content-Range": self.content_range}
                        if self.content_range is not None
                        else {}
                    ),
                },
            )
        raise AssertionError(f"unexpected URL: {url}")


def test_transport_v3_contract_changes_transport_only():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["status"] == "FROZEN_PRE_RESPONSE_TRANSPORT_RETRY"
    prior = contract["supersedes_transport_attempt"]
    assert prior["workflow_run_id"] == 36240304960
    assert prior["outcome"] == "REJECT_PRE_RESPONSE_SCHEMA_OR_GEOMETRY"
    assert prior["response_rows_opened"] == 0
    assert prior["response_values_opened"] is False
    assert prior["scientific_rule_changed"] is False

    transport = contract["transport"]
    assert transport["documented_api_basis"] == "Dryad REST v2 GET /files/{id}/download"
    assert transport["deployment"]["file_id"] == 4788613
    assert transport["sequence"]["file_id"] == 4788614
    assert transport["sequence"]["range"] == "bytes=0-4095"

    unchanged = contract["unchanged_scientific_contract"]
    assert unchanged["focal_taxon"] == "Odocoileus virginianus"
    assert unchanged["states"] == ["solitary", "group"]
    assert unchanged["site_selection_rule_changed"] is False
    assert unchanged["east_holdout_rule_changed"] is False
    assert unchanged["model_changed"] is False


def test_transport_v3_qualifies_api_download_and_206_header_range():
    opener = _Opener()
    result = run_snapshot_usa_transport_v3(opener=opener)

    assert result["status"] == "HEADER_AND_DEPLOYMENT_METADATA_QUALIFIED"
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["deployment"]["selected_site_count"] == 64
    assert result["sequence_header"]["response_rows_opened"] == 0

    trace = result["transport_trace"]
    assert trace["deployment_status"] == 200
    assert trace["sequence_status"] == 206
    assert trace["sequence_content_range"] == "bytes 0-4095/999999"
    assert 0 < trace["sequence_application_bytes_read"] <= 4096

    assert len(opener.requests) == 2
    assert opener.requests[0].full_url.endswith("/api/v2/files/4788613/download")
    assert opener.requests[1].full_url.endswith("/api/v2/files/4788614/download")
    assert opener.requests[1].headers["Range"] == "bytes=0-4095"


def test_transport_v3_stops_before_header_read_if_api_range_is_ignored():
    opener = _Opener(sequence_status=200, content_range=None)
    result = run_snapshot_usa_transport_v3(opener=opener)

    assert result["status"] == "STOP_PRE_RESPONSE_TRANSPORT"
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert "RangeNotHonoredError" in result["transport_error"]
    assert result["transport_trace"]["sequence_status"] == 200
    assert result["transport_trace"]["sequence_application_bytes_read"] == 0


def test_transport_v3_stops_if_deployment_api_is_not_200():
    opener = _Opener(deployment_status=401)
    result = run_snapshot_usa_transport_v3(opener=opener)

    assert result["status"] == "STOP_PRE_RESPONSE_TRANSPORT"
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert "deployment API download returned HTTP 401" in result["transport_error"]
    assert result["transport_trace"]["sequence_status"] is None


def test_transport_v3_has_no_manual_dispatch_and_no_authorization_marker_yet():
    workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "empirical-snapshot-usa-transport-v3-once.yml"
    ).read_text(encoding="utf-8")

    assert "SNAPSHOT_USA_2024_TRANSPORT_V3_RUN_AUTHORIZED" in workflow
    assert "workflow_dispatch" not in workflow
    assert not (
        ROOT
        / "docs"
        / "empirical"
        / "SNAPSHOT_USA_2024_TRANSPORT_V3_RUN_AUTHORIZED"
    ).exists()
