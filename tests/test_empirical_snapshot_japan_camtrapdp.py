import csv
import hashlib
import io
import zipfile

import pytest

from esdm.validate.empirical_snapshot_japan_camtrapdp import (
    EAST_THRESHOLD_LONGITUDE,
    MaskedLogLinearEffort,
    _role,
    build_snapshot_japan_empirical_fixture,
)


def _training_ids():
    wanted = {
        "opportunistic_presence": 18,
        "calibrated_presence": 18,
        "state_annotated": 18,
        "state_calibration": 16,
    }
    result = []
    counts = {key: 0 for key in wanted}
    index = 0
    while sum(counts.values()) < 70:
        value = f"train-{index:04d}"
        role = _role(value)
        if counts[role] < wanted[role]:
            result.append(value)
            counts[role] += 1
        index += 1
    return result


def _csv_bytes(fieldnames, rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _synthetic_package():
    train_ids = _training_ids()
    heldout_ids = [f"held-{index:03d}" for index in range(20)]
    deployment_rows = []
    climate_rows = []

    for index, deployment_id in enumerate(train_ids):
        latitude = 34.0 + index * 0.01
        longitude = 130.0 + index * 0.05
        assert longitude < EAST_THRESHOLD_LONGITUDE
        deployment_rows.append({
            "deploymentID": deployment_id,
            "latitude": latitude,
            "longitude": longitude,
            "deploymentStart": "2023-09-01T00:00:00+09:00",
            "deploymentEnd": "2023-09-15T00:00:00+09:00",
        })
        climate_rows.append({
            "deployment_id": f"safe-{deployment_id}",
            "latitude": latitude,
            "longitude": longitude,
            "partition": "training",
            "bio12_mm": 1000.0 + index,
            "precip_z_train": (index - 34.5) / 20.0,
        })

    for index, deployment_id in enumerate(heldout_ids):
        latitude = 37.0 + index * 0.01
        longitude = 141.0 + index * 0.01
        deployment_rows.append({
            "deploymentID": deployment_id,
            "latitude": latitude,
            "longitude": longitude,
            "deploymentStart": "2023-09-01T00:00:00+09:00",
            "deploymentEnd": "2023-09-15T00:00:00+09:00",
        })
        climate_rows.append({
            "deployment_id": f"safe-{deployment_id}",
            "latitude": latitude,
            "longitude": longitude,
            "partition": "heldout",
            "bio12_mm": 1200.0 + index,
            "precip_z_train": 2.0 + index / 10.0,
        })

    observations = []
    observation_index = 0

    def add_event(deployment_id, count, day=3, hour=3):
        nonlocal observation_index
        observation_index += 1
        observations.append({
            "observationID": f"obs-{observation_index}",
            "deploymentID": deployment_id,
            "eventID": f"event-{observation_index}",
            "eventStart": f"2023-09-{day:02d}T{hour:02d}:00:00+09:00",
            "observationLevel": "event",
            "observationType": "animal",
            "scientificName": "Cervus nippon",
            "count": count,
        })

    by_role = {}
    for deployment_id in train_ids:
        by_role.setdefault(_role(deployment_id), []).append(deployment_id)

    for role in ("opportunistic_presence", "calibrated_presence"):
        for index in range(12):
            add_event(by_role[role][index % len(by_role[role])], 1, day=3 + index % 4)

    for index in range(20):
        add_event(
            by_role["state_annotated"][index % len(by_role["state_annotated"])],
            1 if index < 10 else 2,
            day=4 + index % 4,
        )
        add_event(
            by_role["state_calibration"][index % len(by_role["state_calibration"])],
            1 if index < 10 else 2,
            day=5 + index % 4,
            hour=9,
        )

    for index in range(10):
        add_event(
            heldout_ids[index % len(heldout_ids)],
            1 if index < 5 else 2,
            day=6 + index % 3,
            hour=15,
        )

    deployment_bytes = _csv_bytes(
        (
            "deploymentID",
            "latitude",
            "longitude",
            "deploymentStart",
            "deploymentEnd",
        ),
        deployment_rows,
    )
    observation_bytes = _csv_bytes(
        (
            "observationID",
            "deploymentID",
            "eventID",
            "eventStart",
            "observationLevel",
            "observationType",
            "scientificName",
            "count",
        ),
        observations,
    )
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as writer:
        writer.writestr("deployments.csv", deployment_bytes)
        writer.writestr("observations.csv", observation_bytes)
    payload = archive.getvalue()
    climate = {
        "status": "CLIMATE_QUALIFIED",
        "camera_climate_sha256": "synthetic-climate",
        "camera_climate": climate_rows,
    }
    return payload, climate


def test_masked_loglinear_effort_has_explicit_zero_exposure():
    key = ("a", 1, 3)
    other = ("b", 1, 3)
    effort = MaskedLogLinearEffort(
        exposed_keys=frozenset({key}),
        covariate="season_sin",
        coefficient_parameter="gamma",
    )

    assert effort.structural_exposure_mask((key, other)) == (True, False)
    assert effort.at(
        other,
        theta={"gamma": 0.2},
        covariates={other: {"season_sin": 0.0}},
    ) == 0.0


def test_empirical_fixture_builds_frozen_r5b_streams_from_camtrapdp():
    payload, climate = _synthetic_package()
    fixture = build_snapshot_japan_empirical_fixture(
        camtrapdp_zip=payload,
        climate_payload=climate,
        expected_md5=hashlib.md5(payload).hexdigest(),
    )

    assert len(fixture.train_spaces) == 70
    assert len(fixture.heldout_spaces) == 20
    assert tuple(stream.name for stream in fixture.model.streams) == (
        "presence_opportunistic",
        "presence_calibrated",
        "annotated",
        "state_calibration",
    )
    assert fixture.model.streams[2].state_space.states == ("solitary", "group")
    assert fixture.model.streams[3].state_space.states == ("solitary", "group")
    assert fixture.diagnostics["presence_event_totals"] == {
        "presence_opportunistic": 12,
        "presence_calibrated": 12,
    }
    assert fixture.diagnostics["state_counts"]["training_state_annotated"] == {
        "solitary": 10,
        "group": 10,
    }
    assert fixture.diagnostics["state_counts"]["state_calibration"] == {
        "solitary": 10,
        "group": 10,
    }
    assert fixture.diagnostics["state_counts"]["heldout_state_annotated"] == {
        "solitary": 5,
        "group": 5,
    }

    state_calibration = fixture.model.streams[3]
    heldout_keys = [
        key for key in fixture.model.domain.keys
        if key[0] in set(fixture.heldout_spaces)
    ]
    assert not any(state_calibration.structural_exposure_mask(heldout_keys))


def test_empirical_fixture_fails_closed_when_state_minimum_is_not_met():
    payload, climate = _synthetic_package()
    with pytest.raises(ValueError, match="below frozen minimum"):
        build_snapshot_japan_empirical_fixture(
            camtrapdp_zip=payload,
            climate_payload=climate,
            expected_md5=hashlib.md5(payload).hexdigest(),
            minimum_training_state_count=11,
        )
