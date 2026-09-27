from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import zipfile

import pytest

from esdm.validate.e2_mica_response_blind import qualify_e2_mica_archive
from esdm.validate.e2_mica_worldclim import freeze_e2_mica_worldclim


rasterio = pytest.importorskip("rasterio")


def _deployment_rows():
    rows = []
    for i in range(80):
        rows.append(
            {
                "deploymentID": f"west-{i:03d}",
                "latitude": 51.0 + 0.001 * (i % 10),
                "longitude": 4.0 + 0.0001 * i,
                "deploymentStart": "2025-01-01T00:00:00+00:00",
                "deploymentEnd": "2025-01-31T23:59:59+00:00",
            }
        )
    for i in range(20):
        rows.append(
            {
                "deploymentID": f"east-{i:03d}",
                "latitude": 52.0 + 0.001 * (i % 10),
                "longitude": 8.0 + 0.0001 * i,
                "deploymentStart": "2025-01-01T00:00:00+00:00",
                "deploymentEnd": "2025-01-31T23:59:59+00:00",
            }
        )
    return rows


def _mica_zip(path: Path):
    deployments = io.StringIO()
    writer = csv.DictWriter(
        deployments,
        fieldnames=[
            "deploymentID",
            "latitude",
            "longitude",
            "deploymentStart",
            "deploymentEnd",
        ],
    )
    writer.writeheader()
    writer.writerows(_deployment_rows())

    observations_header = [
        "observationID",
        "deploymentID",
        "eventID",
        "eventStart",
        "observationLevel",
        "observationType",
        "scientificName",
        "count",
    ]
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mica/datapackage.json", json.dumps({"name": "mica"}))
        archive.writestr("mica/deployments.csv", deployments.getvalue())
        archive.writestr("mica/observations.csv", ",".join(observations_header) + "\n")


def _receipt(path: Path):
    result = qualify_e2_mica_archive(path)
    return {
        "result": {
            "status": result["status"],
            "candidate_id": result["candidate_id"],
            "archive_sha256": result["archive"]["sha256"],
            "deployments_sha256": result["archive"]["deployments_sha256"],
            "deployment_count": result["geometry"]["deployment_count"],
            "training_deployment_count": result["geometry"]["training_deployment_count"],
            "heldout_deployment_count": result["geometry"]["heldout_deployment_count"],
            "fingerprints": result["fingerprints"],
        }
    }


def _worldclim_zip(path: Path):
    import numpy as np
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin

    width = 80
    height = 40
    transform = from_origin(3.0, 54.0, 0.1, 0.1)
    values = np.arange(width * height, dtype="float32").reshape(height, width) + 500.0

    with MemoryFile() as memory:
        with memory.open(
            driver="GTiff",
            width=width,
            height=height,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=transform,
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
        tif_bytes = memory.read()

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("wc2.1_10m_bio_12.tif", tif_bytes)


def test_mica_worldclim_freeze_uses_training_only_standardization(tmp_path: Path):
    mica = tmp_path / "mica.zip"
    climate = tmp_path / "worldclim.zip"
    _mica_zip(mica)
    _worldclim_zip(climate)

    result = freeze_e2_mica_worldclim(mica, climate, _receipt(mica))

    assert result["status"] == "CLIMATE_QUALIFIED"
    assert result["training"]["deployment_count"] == 80
    assert result["heldout_deployment_count"] == 20
    assert len(result["deployment_climate"]) == 100

    training = [
        row["precip_z_train"]
        for row in result["deployment_climate"]
        if row["partition"] == "training"
    ]
    mean = sum(training) / len(training)
    variance = sum((value - mean) ** 2 for value in training) / len(training)
    assert mean == pytest.approx(0.0, abs=1e-12)
    assert variance == pytest.approx(1.0, abs=1e-12)


def test_mica_worldclim_freeze_does_not_open_response_rows(tmp_path: Path):
    mica = tmp_path / "mica.zip"
    climate = tmp_path / "worldclim.zip"
    _mica_zip(mica)
    _worldclim_zip(climate)

    result = freeze_e2_mica_worldclim(mica, climate, _receipt(mica))
    firewall = result["response_firewall"]

    assert firewall["scientific_name_values_read"] is False
    assert firewall["count_values_read"] is False
    assert firewall["observation_rows_read_for_climate"] == 0
    assert firewall["focal_taxon_filtering"] is False
    assert firewall["model_fits"] == 0
    assert firewall["heldout_scores"] == 0
    assert firewall["full_response_opened"] is False


def test_mica_worldclim_contract_reuses_frozen_r5b_climate_product():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (
            root
            / "docs"
            / "replication"
            / "E2_MICA_WORLDCLIM_CONTRACT.json"
        ).read_text()
    )

    assert contract["climate_source"]["product"] == (
        "WorldClim v2.1 base bioclimatic variables"
    )
    assert contract["climate_source"]["member"] == "wc2.1_10m_bio_12.tif"
    assert contract["climate_source"]["variable"] == "BIO12 annual precipitation"
    assert contract["preprocessing"]["training_standardization_only"] is True
    assert contract["preprocessing"]["heldout_values_may_not_enter_mean_or_sd"] is True
    assert contract["response_firewall"]["observation_rows_read_for_climate"] == 0
    assert contract["next_stage"]["separate_full_response_authorization_required"] is True
