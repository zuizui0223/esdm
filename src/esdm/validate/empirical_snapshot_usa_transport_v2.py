"""Response-blind Dryad transport retry for Snapshot USA 2024."""
from __future__ import annotations

from dataclasses import dataclass
from http.cookiejar import CookieJar
import json
from pathlib import Path
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPCookieProcessor,
    Request,
    build_opener,
)

from .empirical_snapshot_usa import (
    parse_deployment_metadata,
    parse_sequence_header,
)


CONTRACT_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "empirical"
    / "SNAPSHOT_USA_2024_TRANSPORT_V2_CONTRACT.json"
)


class RangeNotHonoredError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TransportTrace:
    landing_status: int
    deployment_status: int | None
    sequence_status: int | None
    sequence_content_range: str | None
    sequence_application_bytes_read: int


def _contract() -> dict[str, object]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if value["contract_id"] != "empirical-r5b-snapshot-usa-2024-transport-v2":
        raise ValueError("unexpected Snapshot USA transport-v2 contract")
    if value["status"] != "FROZEN_PRE_RESPONSE_TRANSPORT_RETRY":
        raise ValueError("Snapshot USA transport-v2 contract is not frozen")
    return value


def _request_headers(
    cfg: Mapping[str, object],
    *,
    referer: str | None = None,
    range_header: str | None = None,
) -> dict[str, str]:
    headers = {
        "User-Agent": str(cfg["transport"]["user_agent"]),
        "Accept": "text/csv,text/plain;q=0.9,text/html;q=0.8,*/*;q=0.1",
        "Accept-Language": "en-US,en;q=0.8",
        "Cache-Control": "no-cache",
    }
    if referer is not None:
        headers["Referer"] = referer
    if range_header is not None:
        headers["Range"] = range_header
    return headers


def build_session():
    return build_opener(HTTPCookieProcessor(CookieJar()))


def run_snapshot_usa_transport_v2(
    *,
    opener=None,
    contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    cfg = _contract() if contract is None else dict(contract)
    opener = build_session() if opener is None else opener
    dataset = cfg["dataset"]
    transport = cfg["transport"]
    landing_url = str(dataset["landing_url"])

    base = {
        "schema": "esdm.empirical_r5b.snapshot_usa_2024_transport_v2.v1",
        "contract_id": cfg["contract_id"],
        "status": "STOP_PRE_RESPONSE_TRANSPORT",
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "superseded_transport_run_id": int(
            cfg["supersedes_transport_attempt"]["workflow_run_id"]
        ),
    }

    landing_status = None
    deployment_status = None
    sequence_status = None
    content_range = None
    application_bytes = 0

    try:
        landing_request = Request(
            landing_url,
            headers=_request_headers(cfg),
        )
        with opener.open(landing_request, timeout=90) as response:
            landing_status = int(response.getcode())
            if landing_status != 200:
                raise RuntimeError(
                    f"Dryad landing page returned HTTP {landing_status}"
                )
            # Consume only a bounded prefix: enough to establish session/cookies.
            response.read(16384)

        deployment_request = Request(
            str(dataset["deployment_url"]),
            headers=_request_headers(cfg, referer=landing_url),
        )
        with opener.open(deployment_request, timeout=90) as response:
            deployment_status = int(response.getcode())
            if deployment_status != 200:
                raise RuntimeError(
                    f"deployment download returned HTTP {deployment_status}"
                )
            deployment_bytes = response.read()

        deployment = parse_deployment_metadata(
            deployment_bytes,
            contract=json.loads(
                (
                    Path(__file__).resolve().parents[3]
                    / "docs"
                    / "empirical"
                    / "SNAPSHOT_USA_2024_HEADER_CONTRACT.json"
                ).read_text(encoding="utf-8")
            ),
        )

        sequence_cfg = transport["sequence"]
        sequence_request = Request(
            str(dataset["sequence_url"]),
            headers=_request_headers(
                cfg,
                referer=landing_url,
                range_header=str(sequence_cfg["range"]),
            ),
        )
        with opener.open(sequence_request, timeout=90) as response:
            sequence_status = int(response.getcode())
            content_range = response.headers.get("Content-Range")
            if sequence_status != int(sequence_cfg["require_final_http_status"]):
                raise RangeNotHonoredError(
                    f"sequence range returned HTTP {sequence_status}, expected 206"
                )
            if bool(sequence_cfg["require_content_range_header"]) and not content_range:
                raise RangeNotHonoredError(
                    "sequence range response lacks Content-Range"
                )
            maximum = int(sequence_cfg["max_header_bytes"])
            line = response.readline(maximum + 1)
            application_bytes = len(line)
            if len(line) > maximum:
                raise ValueError("sequence header exceeds frozen maximum")
            if not line.endswith((b"\n", b"\r")):
                raise ValueError(
                    "sequence first line did not terminate within frozen range"
                )
            header_bytes = line.rstrip(b"\r\n")

        header = parse_sequence_header(
            header_bytes,
            contract=json.loads(
                (
                    Path(__file__).resolve().parents[3]
                    / "docs"
                    / "empirical"
                    / "SNAPSHOT_USA_2024_HEADER_CONTRACT.json"
                ).read_text(encoding="utf-8")
            ),
        )
    except (HTTPError, URLError, TimeoutError, RangeNotHonoredError, RuntimeError) as exc:
        return {
            **base,
            "transport_error": f"{type(exc).__name__}: {exc}",
            "transport_trace": {
                "landing_status": landing_status,
                "deployment_status": deployment_status,
                "sequence_status": sequence_status,
                "sequence_content_range": content_range,
                "sequence_application_bytes_read": application_bytes,
            },
        }
    except Exception as exc:
        return {
            **base,
            "status": "REJECT_PRE_RESPONSE_SCHEMA_OR_GEOMETRY",
            "qualification_error": f"{type(exc).__name__}: {exc}",
            "transport_trace": {
                "landing_status": landing_status,
                "deployment_status": deployment_status,
                "sequence_status": sequence_status,
                "sequence_content_range": content_range,
                "sequence_application_bytes_read": application_bytes,
            },
        }

    return {
        **base,
        "status": "HEADER_AND_DEPLOYMENT_METADATA_QUALIFIED",
        "transport_error": None,
        "transport_trace": {
            "landing_status": landing_status,
            "deployment_status": deployment_status,
            "sequence_status": sequence_status,
            "sequence_content_range": content_range,
            "sequence_application_bytes_read": application_bytes,
        },
        "deployment": {
            "bytes": len(deployment_bytes),
            **deployment,
        },
        "sequence_header": header,
    }
