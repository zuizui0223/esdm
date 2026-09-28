"""Build an exploratory E3 MICA fixture after the frozen metadata-only repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Mapping

from .e2_mica_full_response import build_e2_mica_empirical_fixture
from .e2_mica_response_blind import qualify_e2_mica_archive
from .e2_mica_temporal_integrity import audit_e2_mica_temporal_integrity
from .e2_mica_worldclim import _canonical_sha256 as _climate_rows_sha256
from .e3_mica_exploratory import (
    audit_nonpositive_deployment_durations,
    sanitize_archive_by_deployment_ids,
)


def _assert_equal(name: str, observed, expected) -> None:
    if observed != expected:
        raise ValueError(f"E3 {name} mismatch: {observed!r} != {expected!r}")


def _response_blind_receipt(qualification: Mapping[str, object]) -> dict[str, object]:
    archive = qualification["archive"]
    geometry = qualification["geometry"]
    roles = qualification["roles"]
    return {
        "result": {
            "status": qualification["status"],
            "candidate_id": qualification["candidate_id"],
            "archive_sha256": archive["sha256"],
            "datapackage_sha256": archive.get("datapackage_sha256"),
            "deployments_sha256": archive["deployments_sha256"],
            "deployment_count": geometry["deployment_count"],
            "training_deployment_count": geometry["training_deployment_count"],
            "heldout_deployment_count": geometry["heldout_deployment_count"],
            "max_training_longitude": geometry["max_training_longitude"],
            "min_heldout_longitude": geometry["min_heldout_longitude"],
            "longitude_gap": geometry["longitude_gap"],
            "strict_east_extrapolation": geometry["strict_east_extrapolation"],
            "training_role_counts": roles["training_counts"],
            "fingerprints": dict(qualification["fingerprints"]),
        }
    }


def _subset_climate_payload(
    climate_payload: Mapping[str, object],
    *,
    excluded_deployment_ids: frozenset[str],
    qualification: Mapping[str, object],
) -> dict[str, object]:
    payload = deepcopy(dict(climate_payload))
    rows = [
        deepcopy(row)
        for row in payload["deployment_climate"]
        if str(row.get("deploymentID", "")).strip() not in excluded_deployment_ids
    ]
    if len(rows) != len(payload["deployment_climate"]) - len(excluded_deployment_ids):
        raise ValueError("E3 climate exclusion did not remove exactly the frozen deployments")
    payload["deployment_climate"] = rows
    payload["deployment_climate_sha256"] = _climate_rows_sha256(rows)
    payload["heldout_deployment_count"] = qualification["geometry"][
        "heldout_deployment_count"
    ]
    return payload


def _adapt_e2_contract(
    e2_full_contract: Mapping[str, object],
    *,
    qualification: Mapping[str, object],
    temporal: Mapping[str, object],
    climate_payload: Mapping[str, object],
) -> dict[str, object]:
    contract = deepcopy(dict(e2_full_contract))
    archive = qualification["archive"]
    geometry = qualification["geometry"]
    fingerprints = qualification["fingerprints"]

    contract["source"]["archive_sha256"] = archive["sha256"]
    contract["source"]["deployments_sha256"] = archive["deployments_sha256"]

    frozen = contract["frozen_partition"]
    frozen["deployment_count"] = geometry["deployment_count"]
    frozen["training_count"] = geometry["training_deployment_count"]
    frozen["heldout_count"] = geometry["heldout_deployment_count"]
    frozen["max_training_longitude"] = geometry["max_training_longitude"]
    frozen["min_heldout_longitude"] = geometry["min_heldout_longitude"]
    frozen["training_ids_sha256"] = fingerprints["training_ids_sha256"]
    frozen["heldout_ids_sha256"] = fingerprints["heldout_ids_sha256"]
    frozen["training_role_map_sha256"] = fingerprints["training_role_map_sha256"]
    frozen["manifest_sha256"] = fingerprints["manifest_sha256"]

    quarantine = temporal["quarantine"]
    contract["temporal_quarantine"]["quarantine_event_count"] = quarantine["event_count"]
    contract["temporal_quarantine"]["quarantine_fraction"] = quarantine[
        "fraction_of_unique_animal_events"
    ]
    contract["temporal_quarantine"]["event_identity_set_sha256"] = quarantine[
        "event_identity_set_sha256"
    ]

    contract["climate"]["deployment_climate_sha256"] = climate_payload[
        "deployment_climate_sha256"
    ]
    return contract


def build_e3_mica_exploratory_fixture(
    *,
    source_archive: str | Path,
    climate_payload: Mapping[str, object],
    e2_full_contract: Mapping[str, object],
    e3_contract: Mapping[str, object],
    preflight_receipt: Mapping[str, object],
):
    """Build the unchanged R5b graph after the frozen E3 metadata-only exclusion."""
    path = Path(source_archive)
    audit = audit_nonpositive_deployment_durations(path)
    frozen = e3_contract["frozen_metadata_audit"]

    _assert_equal(
        "source archive sha256",
        audit["source_sha256"],
        e3_contract["source_boundary"]["source_archive_sha256"],
    )
    _assert_equal(
        "excluded deployment IDs hash",
        audit["excluded_deployment_ids_sha256"],
        frozen["excluded_deployment_ids_sha256"],
    )
    _assert_equal(
        "excluded deployment IDs",
        audit["excluded_deployment_ids"],
        frozen["excluded_deployment_ids"],
    )
    _assert_equal(
        "preflight status",
        preflight_receipt["status"],
        "E3_PREFLIGHT_PASS",
    )

    excluded = frozenset(audit["excluded_deployment_ids"])
    with tempfile.TemporaryDirectory(prefix="esdm-e3-fixture-") as tmp:
        sanitized = Path(tmp) / "mica-e3-sanitized.zip"
        filtering = sanitize_archive_by_deployment_ids(
            path,
            sanitized,
            excluded_deployment_ids=excluded,
        )
        expected_filtering = preflight_receipt["filtering"]
        _assert_equal(
            "removed deployment rows",
            filtering["removed_deployment_rows"],
            expected_filtering["removed_deployment_rows"],
        )
        _assert_equal(
            "removed observation rows",
            filtering["removed_observation_rows"],
            expected_filtering["removed_observation_rows"],
        )

        qualification = qualify_e2_mica_archive(sanitized)
        for name in (
            "training_ids_sha256",
            "heldout_ids_sha256",
            "training_role_map_sha256",
            "manifest_sha256",
        ):
            _assert_equal(
                f"qualification {name}",
                qualification["fingerprints"][name],
                preflight_receipt["qualified_fingerprints"][name],
            )

        response_blind = _response_blind_receipt(qualification)
        temporal = audit_e2_mica_temporal_integrity(
            sanitized,
            response_blind,
        )
        if temporal["status"] != "TEMPORAL_INTEGRITY_PASS":
            raise ValueError(
                f"E3 sanitized temporal integrity failed: {temporal['decision']['stop_reasons']!r}"
            )

        adjusted_climate = _subset_climate_payload(
            climate_payload,
            excluded_deployment_ids=excluded,
            qualification=qualification,
        )
        adapted_contract = _adapt_e2_contract(
            e2_full_contract,
            qualification=qualification,
            temporal=temporal,
            climate_payload=adjusted_climate,
        )

        fixture = build_e2_mica_empirical_fixture(
            archive_path=sanitized,
            climate_payload=adjusted_climate,
            response_blind_receipt=response_blind,
            temporal_receipt=temporal,
            full_contract=adapted_contract,
        )

    diagnostics = dict(fixture.diagnostics)
    diagnostics.update(
        {
            "programme_id": "E3_MICA_EXP",
            "original_source_sha256": audit["source_sha256"],
            "metadata_excluded_deployment_ids": sorted(excluded),
            "metadata_excluded_deployment_ids_sha256": audit[
                "excluded_deployment_ids_sha256"
            ],
            "removed_observation_rows": filtering["removed_observation_rows"],
            "e3_training_deployment_count": qualification["geometry"][
                "training_deployment_count"
            ],
            "e3_heldout_deployment_count": qualification["geometry"][
                "heldout_deployment_count"
            ],
            "e3_training_ids_sha256": qualification["fingerprints"][
                "training_ids_sha256"
            ],
            "e3_heldout_ids_sha256": qualification["fingerprints"][
                "heldout_ids_sha256"
            ],
            "e3_temporal_quarantine_sha256": temporal["quarantine"][
                "event_identity_set_sha256"
            ],
            "e3_adjusted_climate_sha256": adjusted_climate[
                "deployment_climate_sha256"
            ],
            "sanitized_archive_sha256": hashlib.sha256(
                sanitized.read_bytes()
            ).hexdigest() if sanitized.exists() else filtering["sanitized_archive_sha256"],
        }
    )
    return fixture, diagnostics
