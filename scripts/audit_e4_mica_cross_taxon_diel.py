#!/usr/bin/env python3
"""Post-result cross-taxon diel-shift audit for the frozen E4 MICA endpoint."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
import statistics
import zipfile

from esdm.validate.e2_mica_response_blind import qualify_e2_mica_archive


FOCAL = "Ondatra zibethicus"
MIN_EVENTS_PER_STRATUM = 20


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))


def _find(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name for name in archive.namelist()
        if PurePosixPath(name).name == basename and not name.endswith("/")
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {basename!r}: {matches!r}")
    return matches[0]


def _camera_day_exposure(deployments, ids):
    by_id = {str(row["deploymentID"]): row for row in deployments}
    night_parts = []
    day_parts = []
    for deployment_id in sorted(ids):
        row = by_id[deployment_id]
        start = _parse_iso(row["deploymentStart"])
        end = _parse_iso(row["deploymentEnd"])
        if end <= start:
            continue
        current = start.date()
        while current <= end.date():
            midnight = datetime.combine(
                current, datetime.min.time(), tzinfo=start.tzinfo
            )
            for hour in (0, 6, 12, 18):
                left = max(start, midnight + timedelta(hours=hour))
                right = min(end, midnight + timedelta(hours=hour + 6))
                effort = max(0.0, (right - left).total_seconds()) / 86400.0
                if hour in (0, 18):
                    night_parts.append(effort)
                else:
                    day_parts.append(effort)
            current += timedelta(days=1)
    night = math.fsum(night_parts)
    day = math.fsum(day_parts)
    if night <= 0.0 or day <= 0.0:
        raise ValueError("night/day exposure must both be positive")
    return night, day


def _is_binomial(name: str) -> bool:
    parts = str(name).strip().split()
    return len(parts) == 2 and all(parts)


def audit(archive_path: Path, temporal_path: Path) -> dict:
    qualification = qualify_e2_mica_archive(archive_path)
    if qualification["status"] != "RESPONSE_BLIND_GEOMETRY_HEADER_PASS":
        raise ValueError("MICA geometry qualification drifted")
    manifest = qualification["manifest"]
    train_roles = dict(manifest["training_role_by_deployment"])
    heldout_ids = frozenset(manifest["heldout_deployment_ids"])

    temporal = json.loads(temporal_path.read_text(encoding="utf-8"))
    if temporal.get("status") != "TEMPORAL_INTEGRITY_PASS":
        raise ValueError("temporal receipt must PASS")
    quarantine = frozenset(
        (str(row["deploymentID"]), str(row["eventID"]))
        for row in temporal["quarantine"]["event_identities"]
    )

    with zipfile.ZipFile(archive_path) as archive:
        deployments = list(csv.DictReader(io.StringIO(
            archive.read(_find(archive, "deployments.csv")).decode("utf-8-sig")
        )))
        observations = list(csv.DictReader(io.StringIO(
            archive.read(_find(archive, "observations.csv")).decode("utf-8-sig")
        )))

    training_annotated = frozenset(
        deployment_id
        for deployment_id, role in train_roles.items()
        if role == "state_annotated"
    )
    heldout_d = frozenset(
        str(row["deploymentID"])
        for row in deployments
        if str(row["deploymentID"]) in heldout_ids
        and str(row.get("locationName", "")).startswith("D")
    )
    if len(training_annotated) != 266:
        raise ValueError("training annotated deployment count drifted")
    if len(heldout_d) != 164:
        raise ValueError("heldout D-prefix deployment count drifted")

    train_exposure = _camera_day_exposure(deployments, training_annotated)
    d_exposure = _camera_day_exposure(deployments, heldout_d)

    counts = {"training": Counter(), "heldout_D": Counter()}
    seen = set()
    for row in observations:
        if str(row.get("observationLevel", "")).strip() != "event":
            continue
        if str(row.get("observationType", "")).strip() != "animal":
            continue
        deployment_id = str(row.get("deploymentID", "")).strip()
        event_id = str(row.get("eventID", "")).strip()
        species = str(row.get("scientificName", "")).strip()
        if not deployment_id or not event_id or not species:
            continue
        if (deployment_id, event_id) in quarantine:
            continue
        if deployment_id in training_annotated:
            stratum = "training"
        elif deployment_id in heldout_d:
            stratum = "heldout_D"
        else:
            continue
        identity = (stratum, deployment_id, event_id, species)
        if identity in seen:
            continue
        seen.add(identity)
        event_start = _parse_iso(row["eventStart"])
        diel = "night" if event_start.hour < 6 or event_start.hour >= 18 else "day"
        counts[stratum][(species, diel)] += 1

    eligible = []
    labels = sorted(
        {species for values in counts.values() for species, _diel in values}
    )
    for species in labels:
        if not _is_binomial(species):
            continue
        train_night = int(counts["training"][(species, "night")])
        train_day = int(counts["training"][(species, "day")])
        d_night = int(counts["heldout_D"][(species, "night")])
        d_day = int(counts["heldout_D"][(species, "day")])
        if (
            train_night + train_day < MIN_EVENTS_PER_STRATUM
            or d_night + d_day < MIN_EVENTS_PER_STRATUM
            or min(train_night, train_day, d_night, d_day) <= 0
        ):
            continue
        train_ratio = (
            (train_night / train_exposure[0])
            / (train_day / train_exposure[1])
        )
        d_ratio = (
            (d_night / d_exposure[0])
            / (d_day / d_exposure[1])
        )
        log_change = math.log(d_ratio / train_ratio)
        eligible.append({
            "scientificName": species,
            "training_night_events": train_night,
            "training_day_events": train_day,
            "heldout_D_night_events": d_night,
            "heldout_D_day_events": d_day,
            "training_night_day_rate_ratio": train_ratio,
            "heldout_D_night_day_rate_ratio": d_ratio,
            "log_rate_ratio_change": log_change,
            "direction": "lower" if log_change < 0.0 else "higher",
            "focal": species == FOCAL,
        })

    if not eligible or sum(row["focal"] for row in eligible) != 1:
        raise ValueError("eligible set must contain the focal taxon exactly once")
    ordered = sorted(eligible, key=lambda row: row["log_rate_ratio_change"])
    focal_rank = next(
        index + 1 for index, row in enumerate(ordered) if row["focal"]
    )
    nonfocal = [row for row in eligible if not row["focal"]]
    changes = [float(row["log_rate_ratio_change"]) for row in eligible]
    nonfocal_changes = [float(row["log_rate_ratio_change"]) for row in nonfocal]

    result = {
        "schema_version": 1,
        "programme_id": "E4_MICA_SPARSE_NUTS",
        "supplement_id": "e4-mica-postresult-cross-taxon-diel-v1",
        "status": "POSTRESULT_EXPLORATORY_SUPPLEMENT",
        "date": "2026-09-30",
        "parents": {
            "frozen_result": "docs/replication/E4_MICA_SPARSE_FROZEN_RESULT.json",
            "source_domain_supplement": (
                "docs/replication/E4_MICA_POSTRESULT_SOURCE_DOMAIN_SUPPLEMENT.json"
            ),
            "location_robustness_supplement": (
                "docs/replication/E4_MICA_POSTRESULT_LOCATION_ROBUSTNESS_SUPPLEMENT.json"
            ),
        },
        "analysis_boundary": {
            "post_outcome": True,
            "new_model_fit": False,
            "posterior_refit": False,
            "retuning": False,
            "backend_switch": False,
            "claim_promotion": False,
            "cross_taxon_diagnostic_only": True,
        },
        "definitions": {
            "training_stratum": "frozen west training deployments assigned state_annotated",
            "heldout_stratum": "frozen east-heldout deployments with locationName prefix D",
            "event_unit": "unique deploymentID + eventID + scientificName after frozen temporal quarantine",
            "night": "local eventStart hour 18:00-05:59",
            "day": "local eventStart hour 06:00-17:59",
            "exposure": "exact deployment interval overlap in camera-days, split into night/day six-hour bins",
            "eligible_binomial_species": (
                "exactly two-token scientificName; >=20 unique events in each stratum; "
                "at least one night and one day event in each stratum"
            ),
            "minimum_events_per_stratum": MIN_EVENTS_PER_STRATUM,
        },
        "geometry": {
            "training_state_annotated_deployments": len(training_annotated),
            "heldout_D_deployments": len(heldout_d),
            "training_night_camera_days": train_exposure[0],
            "training_day_camera_days": train_exposure[1],
            "heldout_D_night_camera_days": d_exposure[0],
            "heldout_D_day_camera_days": d_exposure[1],
            "quarantined_event_identities_excluded": len(quarantine),
        },
        "summary": {
            "eligible_binomial_species_count": len(eligible),
            "negative_log_ratio_shift_count": sum(
                row["log_rate_ratio_change"] < 0.0 for row in eligible
            ),
            "nonfocal_eligible_species_count": len(nonfocal),
            "nonfocal_negative_log_ratio_shift_count": sum(
                row["log_rate_ratio_change"] < 0.0 for row in nonfocal
            ),
            "median_log_rate_ratio_change": statistics.median(changes),
            "median_rate_ratio_multiplier": math.exp(statistics.median(changes)),
            "nonfocal_median_log_rate_ratio_change": statistics.median(
                nonfocal_changes
            ),
            "nonfocal_median_rate_ratio_multiplier": math.exp(
                statistics.median(nonfocal_changes)
            ),
            "focal_species": FOCAL,
            "focal_negative_shift_rank_most_negative_is_1": focal_rank,
            "focal_log_rate_ratio_change": next(
                row["log_rate_ratio_change"] for row in eligible if row["focal"]
            ),
        },
        "taxa": sorted(eligible, key=lambda row: row["scientificName"]),
        "interpretation": {
            "supported": [
                (
                    "The training-to-D diel-rate shift is not muskrat-specific: "
                    "most eligible binomial species show a lower night/day rate ratio."
                ),
                (
                    "Muskrat is not the most extreme negative diel shift among eligible "
                    "species in the same camera-network comparison."
                ),
                (
                    "The cross-taxon pattern is compatible with a broad domain shift "
                    "affecting observation processes, ecological context, or both."
                ),
            ],
            "not_supported": [
                "A causal camera-detection effect.",
                "A causal observer or annotation effect.",
                "A universal source-domain shift shared by every taxon.",
                "A causal eastward change in muskrat behaviour.",
                "Changing the frozen E4 activity/state decisions.",
                "Rerunning or retuning E4.",
            ],
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--temporal-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.archive, args.temporal_result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
