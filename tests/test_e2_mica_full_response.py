from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import zipfile

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.validate.e2_mica_fit import (
    _annotated_deployment_scores,
    _subset_model,
    _subset_sparse_data,
)
from esdm.validate.e2_mica_full_response import (
    build_e2_mica_empirical_fixture,
)
from esdm.validate.e2_mica_response_blind import (
    _stream_role,
    qualify_e2_mica_archive,
)
from esdm.validate.e2_mica_temporal_integrity import (
    audit_e2_mica_temporal_integrity,
)
from esdm.validate.e2_mica_worldclim import _canonical_sha256


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _ids_by_role():
    output = {
        "opportunistic_presence": [],
        "calibrated_presence": [],
        "state_annotated": [],
        "state_calibration": [],
    }
    index = 0
    while min(len(values) for values in output.values()) < 12:
        deployment_id = f"train-{index:04d}"
        role = _stream_role(deployment_id)
        if len(output[role]) < 12:
            output[role].append(deployment_id)
        index += 1
    return output


def _write_package(tmp_path: Path):
    role_ids = _ids_by_role()
    training = [
        deployment_id
        for role in (
            "opportunistic_presence",
            "calibrated_presence",
            "state_annotated",
            "state_calibration",
        )
        for deployment_id in role_ids[role]
    ]
    # Add enough extra training deployments that the frozen response-blind
    # minimum of 50 is exceeded without altering the selected role exemplars.
    index = 10000
    while len(training) < 60:
        deployment_id = f"train-extra-{index}"
        if deployment_id not in training:
            training.append(deployment_id)
        index += 1
    heldout = [f"heldout-{i:03d}" for i in range(12)]
    all_ids = training + heldout

    deployments = []
    coordinates = {}
    for i, deployment_id in enumerate(training):
        longitude = 4.0 + i * 0.0005
        latitude = 51.0 + (i % 7) * 0.001
        coordinates[deployment_id] = (latitude, longitude)
        deployments.append({
            "deploymentID": deployment_id,
            "latitude": latitude,
            "longitude": longitude,
            "deploymentStart": "2026-01-01T00:00:00+00:00",
            "deploymentEnd": "2026-01-08T00:00:00+00:00",
        })
    for i, deployment_id in enumerate(heldout):
        longitude = 6.0 + i * 0.0005
        latitude = 51.5 + (i % 5) * 0.001
        coordinates[deployment_id] = (latitude, longitude)
        deployments.append({
            "deploymentID": deployment_id,
            "latitude": latitude,
            "longitude": longitude,
            "deploymentStart": "2026-01-01T00:00:00+00:00",
            "deploymentEnd": "2026-01-08T00:00:00+00:00",
        })

    observations = []
    event_index = 0

    def add_event(deployment_id, count, *, species="Ondatra zibethicus"):
        nonlocal event_index
        event_id = f"event-{event_index:04d}"
        event_index += 1
        observations.append({
            "observationID": f"obs-{event_index:04d}",
            "deploymentID": deployment_id,
            "eventID": event_id,
            "eventStart": "2026-01-03T12:00:00+00:00",
            "observationLevel": "event",
            "observationType": "animal",
            "scientificName": species,
            "count": count,
        })

    add_event(role_ids["opportunistic_presence"][0], "")
    add_event(role_ids["calibrated_presence"][0], "")
    add_event(role_ids["state_annotated"][0], "1")
    add_event(role_ids["state_annotated"][0], "2")
    add_event(role_ids["state_calibration"][0], "1")
    add_event(role_ids["state_calibration"][0], "2")
    add_event(heldout[0], "1")
    add_event(heldout[1], "2")
    add_event(heldout[2], "", species="Vulpes vulpes")

    deployment_buffer = io.StringIO()
    writer = csv.DictWriter(
        deployment_buffer,
        fieldnames=[
            "deploymentID",
            "latitude",
            "longitude",
            "deploymentStart",
            "deploymentEnd",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(deployments)

    observation_buffer = io.StringIO()
    writer = csv.DictWriter(
        observation_buffer,
        fieldnames=[
            "observationID",
            "deploymentID",
            "eventID",
            "eventStart",
            "observationLevel",
            "observationType",
            "scientificName",
            "count",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(observations)

    path = tmp_path / "mica.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("deployments.csv", deployment_buffer.getvalue())
        archive.writestr("observations.csv", observation_buffer.getvalue())

    qualified = qualify_e2_mica_archive(path)
    response_blind = {
        "result": {
            "status": qualified["status"],
            "archive_sha256": qualified["archive"]["sha256"],
            "deployments_sha256": qualified["archive"]["deployments_sha256"],
            "deployment_count": qualified["geometry"]["deployment_count"],
            "training_deployment_count": qualified["geometry"][
                "training_deployment_count"
            ],
            "heldout_deployment_count": qualified["geometry"][
                "heldout_deployment_count"
            ],
            "max_training_longitude": qualified["geometry"][
                "max_training_longitude"
            ],
            "min_heldout_longitude": qualified["geometry"][
                "min_heldout_longitude"
            ],
            "longitude_gap": qualified["geometry"]["longitude_gap"],
            "training_role_counts": dict(
                qualified["roles"]["training_counts"]
            ),
            "fingerprints": dict(qualified["fingerprints"]),
        }
    }
    temporal = audit_e2_mica_temporal_integrity(path, response_blind)
    assert temporal["status"] == "TEMPORAL_INTEGRITY_PASS"

    training_ids = tuple(qualified["manifest"]["training_deployment_ids"])
    training_set = set(training_ids)
    raw = {
        deployment_id: 750.0 + index
        for index, deployment_id in enumerate(sorted(all_ids))
    }
    training_values = [raw[deployment_id] for deployment_id in training_ids]
    mean = math.fsum(training_values) / len(training_values)
    sd = math.sqrt(
        math.fsum((value - mean) ** 2 for value in training_values)
        / len(training_values)
    )
    climate_rows = []
    for deployment_id in sorted(all_ids):
        latitude, longitude = coordinates[deployment_id]
        climate_rows.append({
            "deploymentID": deployment_id,
            "latitude": latitude,
            "longitude": longitude,
            "partition": (
                "training" if deployment_id in training_set else "heldout"
            ),
            "bio12_mm": raw[deployment_id],
            "precip_z_train": (raw[deployment_id] - mean) / sd,
        })
    climate = {
        "status": "CLIMATE_QUALIFIED",
        "deployment_climate_sha256": _canonical_sha256(climate_rows),
        "deployment_climate": climate_rows,
    }

    geometry = qualified["geometry"]
    fingerprints = qualified["fingerprints"]
    contract = {
        "source": {"archive_sha256": qualified["archive"]["sha256"]},
        "frozen_partition": {
            "deployment_count": geometry["deployment_count"],
            "training_count": geometry["training_deployment_count"],
            "heldout_count": geometry["heldout_deployment_count"],
            "max_training_longitude": geometry["max_training_longitude"],
            "min_heldout_longitude": geometry["min_heldout_longitude"],
            "training_ids_sha256": fingerprints["training_ids_sha256"],
            "heldout_ids_sha256": fingerprints["heldout_ids_sha256"],
            "training_role_map_sha256": fingerprints[
                "training_role_map_sha256"
            ],
            "manifest_sha256": fingerprints["manifest_sha256"],
        },
        "temporal_quarantine": {
            "event_identity_set_sha256": temporal["quarantine"][
                "event_identity_set_sha256"
            ],
            "quarantine_event_count": temporal["quarantine"]["event_count"],
        },
        "climate": {
            "deployment_climate_sha256": climate[
                "deployment_climate_sha256"
            ]
        },
        "consumed_estimability_stops": {
            "minimum_opportunistic_focal_events": 1,
            "minimum_calibrated_focal_events": 1,
            "minimum_training_state_annotated_each_state": 1,
            "minimum_state_calibration_each_state": 1,
            "minimum_heldout_state_annotated_each_state": 1,
        },
    }
    return path, response_blind, temporal, climate, contract, role_ids, heldout


def _fixture(tmp_path):
    path, response_blind, temporal, climate, contract, _roles, _heldout = (
        _write_package(tmp_path)
    )
    return build_e2_mica_empirical_fixture(
        archive_path=path,
        climate_payload=climate,
        response_blind_receipt=response_blind,
        temporal_receipt=temporal,
        full_contract=contract,
    )


def test_e2_mica_full_response_builds_sparse_r5b_fixture(tmp_path):
    fixture = _fixture(tmp_path)

    assert len(fixture.train_spaces) == 60
    assert len(fixture.heldout_spaces) == 12
    assert fixture.diagnostics["focal_event_count"] == 8
    assert fixture.diagnostics["focal_events_by_role"][
        "opportunistic_presence"
    ] == 1
    assert fixture.diagnostics["focal_events_by_role"][
        "calibrated_presence"
    ] == 1
    assert fixture.diagnostics["state_counts"]["training_state_annotated"] == {
        "solitary": 1,
        "group": 1,
    }
    assert fixture.diagnostics["state_counts"]["state_calibration"] == {
        "solitary": 1,
        "group": 1,
    }
    assert fixture.diagnostics["state_counts"]["heldout_state_annotated"] == {
        "solitary": 1,
        "group": 1,
    }

    # Response maps are sparse: no zero-filled full grid is materialized.
    positive_entries = sum(
        len(values)
        for values in fixture.data["annotated"]["sp"].values()
    )
    assert positive_entries == 4
    assert positive_entries < fixture.diagnostics["grid_context_count"]


def test_e2_mica_count_conflict_is_consumed_hard_stop(tmp_path):
    path, response_blind, temporal, climate, contract, roles, _heldout = (
        _write_package(tmp_path)
    )
    with zipfile.ZipFile(path, "r") as source:
        deployments = source.read("deployments.csv")
        observations = source.read("observations.csv").decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(observations)))
    target = roles["state_annotated"][0]
    event = next(row for row in rows if row["deploymentID"] == target)
    duplicate = dict(event)
    duplicate["observationID"] = "obs-conflict"
    duplicate["count"] = "3"
    rows.append(duplicate)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    conflict = tmp_path / "conflict.zip"
    with zipfile.ZipFile(conflict, "w", compression=zipfile.ZIP_DEFLATED) as out:
        out.writestr("deployments.csv", deployments)
        out.writestr("observations.csv", buffer.getvalue())

    # Re-freeze transport/temporal hashes for this synthetic-only unit world so the
    # test reaches the MICA child-contract count conflict itself.
    qualified = qualify_e2_mica_archive(conflict)
    response_blind = {
        "result": {
            "status": qualified["status"],
            "archive_sha256": qualified["archive"]["sha256"],
            "deployments_sha256": qualified["archive"]["deployments_sha256"],
            "deployment_count": qualified["geometry"]["deployment_count"],
            "training_deployment_count": qualified["geometry"][
                "training_deployment_count"
            ],
            "heldout_deployment_count": qualified["geometry"][
                "heldout_deployment_count"
            ],
            "max_training_longitude": qualified["geometry"][
                "max_training_longitude"
            ],
            "min_heldout_longitude": qualified["geometry"][
                "min_heldout_longitude"
            ],
            "longitude_gap": qualified["geometry"]["longitude_gap"],
            "training_role_counts": dict(
                qualified["roles"]["training_counts"]
            ),
            "fingerprints": dict(qualified["fingerprints"]),
        }
    }
    temporal = audit_e2_mica_temporal_integrity(conflict, response_blind)
    contract["source"]["archive_sha256"] = qualified["archive"]["sha256"]
    contract["temporal_quarantine"] = {
        "event_identity_set_sha256": temporal["quarantine"][
            "event_identity_set_sha256"
        ],
        "quarantine_event_count": temporal["quarantine"]["event_count"],
    }

    with pytest.raises(ValueError, match="conflicting positive counts"):
        build_e2_mica_empirical_fixture(
            archive_path=conflict,
            climate_payload=climate,
            response_blind_receipt=response_blind,
            temporal_receipt=temporal,
            full_contract=contract,
        )


def test_e2_mica_subset_data_remains_sparse(tmp_path):
    fixture = _fixture(tmp_path)
    train, _ = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout=None,
    )
    data = _subset_sparse_data(fixture, train)
    assert len(data["presence_opportunistic"]["sp"]) == 1
    assert len(data["presence_calibrated"]["sp"]) == 1
    assert all(
        key[0] in set(fixture.train_spaces)
        for key in data["presence_opportunistic"]["sp"]
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_e2_mica_row_scores_equal_aggregate_by_construction(tmp_path):
    fixture = _fixture(tmp_path)
    heldout_model, heldout_covariates = _subset_model(
        fixture,
        fixture.heldout_spaces,
        knockout=None,
    )
    heldout_data = _subset_sparse_data(fixture, heldout_model)

    samples = {}
    for species, processes in heldout_model.species.items():
        for process in processes:
            for parameter, prior in process.priors().items():
                assert prior.distribution == "Normal"
                samples[f"{species}.{process.name}.{parameter}"] = [0.0, 0.0]

    aggregate, rows = _annotated_deployment_scores(
        heldout_model,
        samples,
        heldout_covariates,
        heldout_data,
        chunk_size=1,
    )
    assert len(rows) == 12
    assert math.isfinite(aggregate)
    assert aggregate == pytest.approx(
        math.fsum(row["score"] for row in rows) / len(rows),
        abs=1e-12,
    )
