from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from esdm.validate.empirical_snapshot_usa import _stream_bucket
from esdm.validate.empirical_snapshot_usa_transport_v2 import (
    run_snapshot_usa_transport_v2,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_USA_2024_TRANSPORT_V2_CONTRACT.json"


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
    def __init__(self, *, sequence_status=206, content_range="bytes 0-4095/999999"):
        self.sequence_status = sequence_status
        self.content_range = content_range
        self.requests = []

    def open(self, request, timeout=90):
        self.requests.append(request)
        url = request.full_url
        if "/dataset/" in url:
            return _Response(status=200, body=b"<html>Dryad</html>")
        if url.endswith("4788613"):
            return _Response(status=200, body=_deployment_csv())
        if url.endswith("4788614"):
            return _Response(
                status=self.sequence_status,
                body=_sequence_header(),
                headers=(
                    {"Content-Range": self.content_range}
                    if self.content_range is not None
                    else {}
                ),
            )
        raise AssertionError(f"unexpected URL: {url}")


def test_transport_v2_contract_preserves_failed_v1_and_scientific_rules():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["status"] == "FROZEN_PRE_RESPONSE_TRANSPORT_RETRY"
    prior = contract["supersedes_transport_attempt"]
    assert prior["workflow_run_id"] == 36229789655
    assert prior["outcome"] == "STOP_PRE_RESPONSE_TRANSPORT"
    assert prior["response_rows_opened"] == 0
    assert prior["response_values_opened"] is False
    assert prior["scientific_rule_changed"] is False

    unchanged = contract["unchanged_scientific_contract"]
    assert unchanged["focal_taxon"] == "Odocoileus virginianus"
    assert unchanged["states"] == ["solitary", "group"]
    assert unchanged["site_selection_rule_changed"] is False
    assert unchanged["east_holdout_rule_changed"] is False
    assert unchanged["model_changed"] is False


def test_transport_v2_qualifies_only_after_cookie_session_and_206_range():
    opener = _Opener()
    result = run_snapshot_usa_transport_v2(opener=opener)

    assert result["status"] == "HEADER_AND_DEPLOYMENT_METADATA_QUALIFIED"
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["deployment"]["selected_site_count"] == 64
    assert len(result["deployment"]["selected_sites"]) == 64
    assert result["deployment"]["selected_deployments"]
    assert result["sequence_header"]["response_rows_opened"] == 0

    trace = result["transport_trace"]
    assert trace["landing_status"] == 200
    assert trace["deployment_status"] == 200
    assert trace["sequence_status"] == 206
    assert trace["sequence_content_range"] == "bytes 0-4095/999999"
    assert 0 < trace["sequence_application_bytes_read"] <= 4096

    assert len(opener.requests) == 3
    assert opener.requests[2].headers["Range"] == "bytes=0-4095"
    assert "Referer" in opener.requests[1].headers
    assert "Referer" in opener.requests[2].headers


def test_transport_v2_stops_without_reading_header_if_range_is_ignored():
    opener = _Opener(sequence_status=200, content_range=None)
    result = run_snapshot_usa_transport_v2(opener=opener)

    assert result["status"] == "STOP_PRE_RESPONSE_TRANSPORT"
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert "RangeNotHonoredError" in result["transport_error"]
    assert result["transport_trace"]["sequence_status"] == 200
    assert result["transport_trace"]["sequence_application_bytes_read"] == 0


def test_transport_v2_stops_if_206_lacks_content_range():
    opener = _Opener(sequence_status=206, content_range=None)
    result = run_snapshot_usa_transport_v2(opener=opener)

    assert result["status"] == "STOP_PRE_RESPONSE_TRANSPORT"
    assert result["response_rows_opened"] == 0
    assert "Content-Range" in result["transport_error"]


def test_transport_v2_has_no_manual_dispatch_and_no_authorization_marker_yet():
    workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "empirical-snapshot-usa-transport-v2-once.yml"
    ).read_text(encoding="utf-8")

    assert "SNAPSHOT_USA_2024_TRANSPORT_V2_RUN_AUTHORIZED" in workflow
    assert "workflow_dispatch" not in workflow
    assert not (
        ROOT
        / "docs"
        / "empirical"
        / "SNAPSHOT_USA_2024_TRANSPORT_V2_RUN_AUTHORIZED"
    ).exists()
