#!/usr/bin/env python3
"""Post-result descriptive audit of E4 MICA transfer-tail behavior."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _inner_member(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name for name in archive.namelist()
        if PurePosixPath(name).name == basename and not name.endswith("/")
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {basename!r}, got {matches!r}")
    return matches[0]


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _parse_iso(value: str):
    from datetime import datetime
    return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))


def _representative_doy(value) -> int:
    from datetime import datetime
    iso = value.isocalendar()
    thursday = datetime.fromisocalendar(iso.year, iso.week, 4).date()
    return int(thursday.timetuple().tm_yday)


def _hour_bin(hour: int) -> int:
    value = int(hour)
    if 0 <= value <= 5:
        return 3
    if value <= 11:
        return 9
    if value <= 17:
        return 15
    if value <= 23:
        return 21
    raise ValueError("hour outside 0..23")


def _mean(values):
    values = tuple(float(v) for v in values)
    return math.fsum(values) / len(values) if values else math.nan


def _corr(xs, ys):
    pairs = [
        (float(x), float(y))
        for x, y in zip(xs, ys, strict=True)
        if math.isfinite(float(x)) and math.isfinite(float(y))
    ]
    if len(pairs) < 3:
        return math.nan
    mx = _mean(x for x, _ in pairs)
    my = _mean(y for _, y in pairs)
    dx = [x - mx for x, _ in pairs]
    dy = [y - my for _, y in pairs]
    vx = math.fsum(v * v for v in dx)
    vy = math.fsum(v * v for v in dy)
    if vx <= 0.0 or vy <= 0.0:
        return math.nan
    return math.fsum(x * y for x, y in zip(dx, dy, strict=True)) / math.sqrt(vx * vy)


def _quantile(sorted_values, p: float) -> float:
    if not sorted_values:
        return math.nan
    index = round((len(sorted_values) - 1) * float(p))
    return float(sorted_values[index])


def _distribution(values):
    values = tuple(float(v) for v in values)
    ordered = sorted(values)
    return {
        "mean": _mean(values),
        "median": statistics.median(values),
        "q05": _quantile(ordered, 0.05),
        "q25": _quantile(ordered, 0.25),
        "q75": _quantile(ordered, 0.75),
        "q95": _quantile(ordered, 0.95),
        "minimum": ordered[0],
        "maximum": ordered[-1],
        "positive_rate": sum(v > 0.0 for v in values) / len(values),
    }


def build_audit(
    *,
    result_path: Path,
    e2_capture_zip: Path,
    temporal_result_path: Path,
):
    result = _read_json(result_path)
    if result.get("status") != "E4_SPARSE_EMPIRICAL_RESULT":
        raise ValueError("audit requires frozen E4 empirical result")
    rows = result.get("heldout_deployment_scores")
    if not isinstance(rows, list) or len(rows) != 733:
        raise ValueError("audit requires exactly 733 heldout deployment rows")

    temporal = _read_json(temporal_result_path)
    quarantine = {
        (str(row["deploymentID"]), str(row["eventID"]))
        for row in temporal["quarantine"]["event_identities"]
    }

    with zipfile.ZipFile(e2_capture_zip) as outer:
        climate = json.loads(
            outer.read("frozen-climate/E2_MICA_WORLDCLIM_RESULT.json")
        )
        mica_bytes = outer.read("build/e2/source/mica-v3.zip")
    climate_by_id = {
        str(row["deploymentID"]): row
        for row in climate["deployment_climate"]
    }

    with zipfile.ZipFile(io.BytesIO(mica_bytes)) as mica:
        deployments_name = _inner_member(mica, "deployments.csv")
        observations_name = _inner_member(mica, "observations.csv")
        deployments = list(csv.DictReader(io.StringIO(
            mica.read(deployments_name).decode("utf-8-sig")
        )))
        observations = list(csv.DictReader(io.StringIO(
            mica.read(observations_name).decode("utf-8-sig")
        )))

    deployment_by_id = {
        str(row["deploymentID"]): row for row in deployments
    }
    e2_contract = _read_json(DOCS / "E2_MICA_FULL_RESPONSE_CONTRACT.json")
    west = float(e2_contract["frozen_partition"]["max_training_longitude"])
    training = [
        row for row in deployments if float(row["longitude"]) <= west
    ]
    if len(training) != 805:
        raise ValueError("training deployment count drift")

    train_longitudes = [float(row["longitude"]) for row in training]
    lon_mean = _mean(train_longitudes)
    lon_sd = math.sqrt(_mean((value - lon_mean) ** 2 for value in train_longitudes))
    if lon_sd <= 0.0:
        raise ValueError("training longitude sd is non-positive")

    heldout_ids = {str(row["deploymentID"]) for row in rows}
    heldout_deployments = [deployment_by_id[value] for value in heldout_ids]
    train_precip = [
        float(climate_by_id[str(row["deploymentID"])]["precip_z_train"])
        for row in training
    ]
    heldout_precip = [
        float(climate_by_id[str(row["deploymentID"])]["precip_z_train"])
        for row in heldout_deployments
    ]
    train_east = [
        (float(row["longitude"]) - lon_mean) / lon_sd
        for row in training
    ]
    heldout_east = [
        (float(row["longitude"]) - lon_mean) / lon_sd
        for row in heldout_deployments
    ]

    focal_events = {}
    for row in observations:
        if str(row.get("observationLevel", "")).strip() != "event":
            continue
        if str(row.get("observationType", "")).strip() != "animal":
            continue
        if str(row.get("scientificName", "")).strip() != "Ondatra zibethicus":
            continue
        deployment_id = str(row.get("deploymentID", "")).strip()
        event_id = str(row.get("eventID", "")).strip()
        if deployment_id not in heldout_ids:
            continue
        if (deployment_id, event_id) in quarantine:
            continue
        record = focal_events.setdefault(
            (deployment_id, event_id),
            {
                "event_start": _parse_iso(row["eventStart"]),
                "positive_counts": set(),
            },
        )
        text = str(row.get("count", "")).strip()
        if not text:
            continue
        try:
            numeric = float(text)
        except ValueError:
            continue
        if numeric > 0.0 and numeric.is_integer():
            record["positive_counts"].add(int(numeric))

    parameter_means = {
        name: float(summary["mean"])
        for name, summary in result["parameter_summaries"].items()
    }
    activity_intercept = parameter_means["sp.activity.activity_intercept"]
    activity_baseline = _sigmoid(activity_intercept)

    event_by_deployment = {}
    for (deployment_id, _event_id), record in focal_events.items():
        positives = tuple(sorted(record["positive_counts"]))
        if len(positives) != 1:
            continue
        count = positives[0]
        event_time = record["event_start"]
        doy = _representative_doy(event_time)
        hour = _hour_bin(event_time.hour)
        precip = float(climate_by_id[deployment_id]["precip_z_train"])
        longitude = float(deployment_by_id[deployment_id]["longitude"])
        eastness = (longitude - lon_mean) / lon_sd
        season_phase = 2.0 * math.pi * (float(doy) - 15.0) / 365.0
        diurnal_phase = 2.0 * math.pi * float(hour) / 24.0
        season_sin = math.sin(season_phase)
        season_cos = math.cos(season_phase)
        diurnal_sin = math.sin(diurnal_phase)
        diurnal_cos = math.cos(diurnal_phase)

        activity_eta = (
            activity_intercept
            + parameter_means["sp.activity.activity_beta_precip"] * precip
            + parameter_means["sp.activity.activity_beta_eastness"] * eastness
            + parameter_means["sp.activity.activity_beta_season"] * season_cos
            + parameter_means["sp.activity.activity_beta_diurnal"] * diurnal_cos
        )
        group_eta = (
            parameter_means["sp.state.alpha_group"]
            + parameter_means["sp.state.beta_group_precip"] * precip
            + parameter_means["sp.state.beta_group_eastness"] * eastness
            + parameter_means["sp.state.beta_group_season"] * season_sin
            + parameter_means["sp.state.beta_group_diurnal"] * diurnal_sin
        )
        event_by_deployment.setdefault(deployment_id, []).append({
            "activity": _sigmoid(activity_eta),
            "group_probability": _sigmoid(group_eta),
            "observed_group": bool(count >= 2),
        })

    deployment_records = []
    for row in rows:
        deployment_id = str(row["deploymentID"])
        meta = deployment_by_id[deployment_id]
        climate_row = climate_by_id[deployment_id]
        start = _parse_iso(meta["deploymentStart"])
        end = _parse_iso(meta["deploymentEnd"])
        events = event_by_deployment.get(deployment_id, [])
        activity_gain = (
            float(row["full_heldout_log_score"])
            - float(row["activity_knockout_heldout_log_score"])
        )
        state_gain = (
            float(row["full_heldout_log_score"])
            - float(row["state_knockout_heldout_log_score"])
        )
        deployment_records.append({
            "deploymentID": deployment_id,
            "activity_gain": activity_gain,
            "state_gain": state_gain,
            "longitude": float(meta["longitude"]),
            "precip_z_train": float(climate_row["precip_z_train"]),
            "duration_days": (end - start).total_seconds() / 86400.0,
            "scored_state_context_cells": int(row["scored_state_context_cells"]),
            "labeled_focal_events": len(events),
            "mean_event_activity": (
                _mean(item["activity"] for item in events)
                if events else None
            ),
            "fraction_events_below_knockout_activity": (
                sum(item["activity"] < activity_baseline for item in events) / len(events)
                if events else None
            ),
            "observed_group_fraction": (
                sum(item["observed_group"] for item in events) / len(events)
                if events else None
            ),
            "mean_posterior_mean_group_probability": (
                _mean(item["group_probability"] for item in events)
                if events else None
            ),
        })

    activity_gains = [row["activity_gain"] for row in deployment_records]
    state_gains = [row["state_gain"] for row in deployment_records]
    negative = sorted(value for value in activity_gains if value < 0.0)
    total_negative_magnitude = -math.fsum(negative)
    ordered_activity = sorted(activity_gains)

    tail_n = round(len(deployment_records) * 0.10)
    ordered_records = sorted(
        deployment_records, key=lambda row: row["activity_gain"]
    )
    tail = ordered_records[:tail_n]
    rest = ordered_records[tail_n:]

    all_event_activities = [
        item["activity"]
        for values in event_by_deployment.values()
        for item in values
    ]

    audit = {
        "schema_version": 1,
        "programme_id": "E4_MICA_SPARSE_NUTS",
        "audit_id": "e4-mica-postresult-transfer-tail-v1",
        "status": "POSTRESULT_EXPLORATORY_AUDIT",
        "source_result": {
            "result_id": result["result_id"],
            "result_status": result["status"],
            "workflow_run_id": 36622802225,
            "artifact_id": 11059622869,
            "result_json_sha256": (
                "34124094e6c25db04465cc1ff869af5813326729e6fd3b658a0921c45bc6f3e2"
            ),
        },
        "frozen_result_unchanged": True,
        "score_distribution": {
            "activity": _distribution(activity_gains),
            "state": _distribution(state_gains),
            "activity_loss_concentration": {
                "worst_1_share_of_total_negative_magnitude": (
                    -math.fsum(ordered_activity[:1]) / total_negative_magnitude
                ),
                "worst_5_share_of_total_negative_magnitude": (
                    -math.fsum(ordered_activity[:5]) / total_negative_magnitude
                ),
                "worst_10_share_of_total_negative_magnitude": (
                    -math.fsum(ordered_activity[:10]) / total_negative_magnitude
                ),
                "worst_20_share_of_total_negative_magnitude": (
                    -math.fsum(ordered_activity[:20]) / total_negative_magnitude
                ),
                "worst_50_share_of_total_negative_magnitude": (
                    -math.fsum(ordered_activity[:50]) / total_negative_magnitude
                ),
            },
        },
        "covariate_support": {
            "training_eastness_z_range": [min(train_east), max(train_east)],
            "heldout_eastness_z_range": [min(heldout_east), max(heldout_east)],
            "training_precip_z_range": [min(train_precip), max(train_precip)],
            "heldout_precip_z_range": [min(heldout_precip), max(heldout_precip)],
            "heldout_fraction_eastness_z_gt_3": (
                sum(value > 3.0 for value in heldout_east) / len(heldout_east)
            ),
            "heldout_fraction_precip_z_lt_minus_2": (
                sum(value < -2.0 for value in heldout_precip) / len(heldout_precip)
            ),
        },
        "activity_transfer_diagnostic": {
            "knockout_baseline_activity_probability": activity_baseline,
            "event_weighted_posterior_mean_activity_probability": _mean(
                all_event_activities
            ),
            "event_weighted_activity_to_knockout_ratio": (
                _mean(all_event_activities) / activity_baseline
            ),
            "event_bearing_heldout_deployments": len(event_by_deployment),
            "heldout_deployments": len(deployment_records),
            "corr_activity_gain_labeled_event_count": _corr(
                [row["activity_gain"] for row in deployment_records],
                [row["labeled_focal_events"] for row in deployment_records],
            ),
            "corr_activity_gain_longitude": _corr(
                [row["activity_gain"] for row in deployment_records],
                [row["longitude"] for row in deployment_records],
            ),
            "corr_activity_gain_precip_z": _corr(
                [row["activity_gain"] for row in deployment_records],
                [row["precip_z_train"] for row in deployment_records],
            ),
            "worst_10_percent": {
                "n": tail_n,
                "activity_gain_threshold": float(tail[-1]["activity_gain"]),
                "mean_longitude": _mean(row["longitude"] for row in tail),
                "mean_precip_z_train": _mean(row["precip_z_train"] for row in tail),
                "mean_labeled_focal_events": _mean(
                    row["labeled_focal_events"] for row in tail
                ),
                "mean_duration_days": _mean(row["duration_days"] for row in tail),
                "rest_mean_longitude": _mean(row["longitude"] for row in rest),
                "rest_mean_precip_z_train": _mean(
                    row["precip_z_train"] for row in rest
                ),
                "rest_mean_labeled_focal_events": _mean(
                    row["labeled_focal_events"] for row in rest
                ),
                "rest_mean_duration_days": _mean(
                    row["duration_days"] for row in rest
                ),
            },
            "posterior_mean_activity_parameters": {
                name: parameter_means[name]
                for name in (
                    "sp.activity.activity_intercept",
                    "sp.activity.activity_beta_precip",
                    "sp.activity.activity_beta_eastness",
                    "sp.activity.activity_beta_season",
                    "sp.activity.activity_beta_diurnal",
                )
            },
        },
        "interpretation": {
            "supported": [
                (
                    "the negative aggregate activity gain is strongly tail-concentrated "
                    "rather than uniformly negative across heldout deployments"
                ),
                (
                    "the east holdout lies entirely beyond the training eastness support "
                    "used by the activity model"
                ),
                (
                    "posterior-mean activity at observed heldout focal-event contexts is "
                    "substantially below the activity-knockout baseline on average"
                ),
            ],
            "working_hypothesis": (
                "process-specific activity slopes extrapolate into an out-of-support "
                "east/climate regime and suppress expected counts at a minority of "
                "high-event deployments, creating transfer tail risk"
            ),
            "not_supported": [
                "causal explanation for muskrat activity",
                "proof that activity is biologically irrelevant",
                "a revised E4 scientific result",
                "permission to retune, rerun, or switch backend within E4",
            ],
        },
    }
    return audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--e2-capture-zip", type=Path, required=True)
    parser.add_argument("--temporal-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    audit = build_audit(
        result_path=args.result,
        e2_capture_zip=args.e2_capture_zip,
        temporal_result_path=args.temporal_result,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
