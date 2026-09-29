"""Build an exploratory E3 MICA fixture after the frozen metadata-only repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Mapping

from esdm.model import Model

from .e2_mica_full_response import (
    E2MicaEmpiricalFixture,
    build_e2_mica_empirical_fixture,
)
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
    materialize_state_calibration_failure: bool = False,
):
    """Build the R5b graph after the frozen E3 metadata-only exclusion.

    The materialization flag is an implementation-only escape hatch used by
    the separately frozen reduced endpoint. It bypasses the E2 numerical
    minimum solely long enough to materialize the fixed parsed data; callers
    must remove the direct state-calibration stream before fitting.
    """
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
        original_state_calibration_minimum = int(
            e2_full_contract["consumed_estimability_stops"][
                "minimum_state_calibration_each_state"
            ]
        )
        if materialize_state_calibration_failure:
            adapted_contract["consumed_estimability_stops"][
                "minimum_state_calibration_each_state"
            ] = 0

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
            "sanitized_archive_sha256": filtering["sanitized_archive_sha256"],
            "original_minimum_state_calibration_each_state": (
                original_state_calibration_minimum
            ),
            "materialization_only_state_calibration_gate_bypass": bool(
                materialize_state_calibration_failure
            ),
        }
    )
    return fixture, diagnostics


def build_e3_mica_reduced_fixture(
    *,
    source_archive: str | Path,
    climate_payload: Mapping[str, object],
    e2_full_contract: Mapping[str, object],
    e3_contract: Mapping[str, object],
    preflight_receipt: Mapping[str, object],
    reduced_contract: Mapping[str, object],
) -> tuple[E2MicaEmpiricalFixture, dict[str, object]]:
    """Materialize fixed E3 data, then remove direct state calibration before fitting."""
    if reduced_contract["endpoint_id"] != (
        "E3_MICA_REDUCED_NO_DIRECT_STATE_CALIBRATION"
    ):
        raise ValueError("unexpected E3 reduced endpoint contract")
    reduced = reduced_contract["reduced_endpoint"]
    if reduced["change"] != (
        "remove the state_calibration stream entirely before any model fitting"
    ):
        raise ValueError("E3 reduced endpoint change drifted")
    if reduced["lower_state_calibration_minimum"] is not False:
        raise ValueError("E3 reduced endpoint may not lower the calibration minimum")
    if reduced["reuse_state_calibration_rows_in_other_streams"] is not False:
        raise ValueError("E3 reduced endpoint may not reuse calibration rows")
    if reduced["reassign_training_roles"] is not False:
        raise ValueError("E3 reduced endpoint may not reassign training roles")

    fixture, diagnostics = build_e3_mica_exploratory_fixture(
        source_archive=source_archive,
        climate_payload=climate_payload,
        e2_full_contract=e2_full_contract,
        e3_contract=e3_contract,
        preflight_receipt=preflight_receipt,
        materialize_state_calibration_failure=True,
    )

    frozen_stop = reduced_contract["full_endpoint_stop"]
    state_counts = diagnostics["state_counts"]
    focal_by_role = diagnostics["focal_events_by_role"]
    expected_states = frozen_stop["other_state_counts"]

    _assert_equal(
        "training state-annotated counts",
        state_counts["training_state_annotated"],
        expected_states["training_state_annotated"],
    )
    _assert_equal(
        "state-calibration counts",
        state_counts["state_calibration"],
        frozen_stop["observed_state_calibration"],
    )
    _assert_equal(
        "heldout state-annotated counts",
        state_counts["heldout_state_annotated"],
        expected_states["heldout_state_annotated"],
    )
    _assert_equal(
        "focal events by role",
        focal_by_role,
        frozen_stop["focal_events_by_role"],
    )
    _assert_equal(
        "total focal events",
        diagnostics["focal_event_count"],
        frozen_stop["total_focal_events"],
    )

    original_minimum = int(
        e2_full_contract["consumed_estimability_stops"][
            "minimum_state_calibration_each_state"
        ]
    )
    _assert_equal(
        "frozen state-calibration minimum",
        original_minimum,
        frozen_stop["frozen_minimum_state_calibration_each_state"],
    )
    observed_group = int(state_counts["state_calibration"]["group"])
    if not observed_group < original_minimum:
        raise ValueError(
            "E3 reduced endpoint requires the frozen full endpoint to fail "
            "the group state-calibration minimum"
        )

    retained_streams = tuple(
        stream for stream in fixture.model.streams
        if stream.name != "state_calibration"
    )
    removed = tuple(
        stream for stream in fixture.model.streams
        if stream.name == "state_calibration"
    )
    if len(removed) != 1:
        raise ValueError(
            "E3 reduced endpoint must remove exactly one state_calibration stream"
        )
    if any(stream.name == "state_calibration" for stream in retained_streams):
        raise AssertionError("state_calibration stream survived reduced endpoint")

    reduced_model = Model(
        domain=fixture.model.domain,
        species=fixture.model.species,
        streams=retained_streams,
    )
    reduced_model.check_design()

    reduced_data = {
        name: value
        for name, value in fixture.data.items()
        if name != "state_calibration"
    }
    if "state_calibration" in reduced_data:
        raise AssertionError("state_calibration data survived reduced endpoint")

    diagnostics = dict(diagnostics)
    diagnostics.update(
        {
            "endpoint_id": reduced_contract["endpoint_id"],
            "full_endpoint_state_calibration_gate_passed": False,
            "full_endpoint_observed_state_calibration_group": observed_group,
            "full_endpoint_required_state_calibration_group": original_minimum,
            "materialization_only_state_calibration_gate_bypass": True,
            "state_calibration_stream_present_in_fit": False,
            "state_calibration_rows_reused": False,
            "training_roles_reassigned": False,
            "reduced_model_streams": [
                stream.name for stream in reduced_model.streams
            ],
        }
    )

    reduced_fixture = E2MicaEmpiricalFixture(
        model=reduced_model,
        covariates=fixture.covariates,
        data=reduced_data,
        train_spaces=fixture.train_spaces,
        heldout_spaces=fixture.heldout_spaces,
        stream_by_space=fixture.stream_by_space,
        source_sha256=fixture.source_sha256,
        climate_sha256=fixture.climate_sha256,
        diagnostics=diagnostics,
    )
    return reduced_fixture, diagnostics
