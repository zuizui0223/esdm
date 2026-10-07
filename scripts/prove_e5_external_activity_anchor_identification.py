#!/usr/bin/env python3
"""Response-free structural identification proof for the external activity-anchor route."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable


def _positive_vector(values: Iterable[float]) -> list[float]:
    out = [float(v) for v in values]
    if not out or any((not math.isfinite(v)) or v <= 0 for v in out):
        raise ValueError("positive finite 1D vector required")
    return out


def normalize_simplex(values: Iterable[float]) -> list[float]:
    x = _positive_vector(values)
    total = sum(x)
    return [v / total for v in x]


def normalize_log_shape(values: Iterable[float]) -> list[float]:
    d = _positive_vector(values)
    logs = [math.log(v) for v in d]
    center = sum(logs) / len(logs)
    return [math.exp(v - center) for v in logs]


def camera_shape(activity: Iterable[float], distortion: Iterable[float]) -> list[float]:
    a = normalize_simplex(activity)
    d = _positive_vector(distortion)
    if len(a) != len(d):
        raise ValueError("matching vectors required")
    return normalize_simplex([av * dv for av, dv in zip(a, d)])


def recover_relative_distortion(
    activity: Iterable[float],
    camera: Iterable[float],
) -> list[float]:
    a = normalize_simplex(activity)
    c = normalize_simplex(camera)
    if len(a) != len(c):
        raise ValueError("matching vectors required")
    raw = [math.log(cv) - math.log(av) for av, cv in zip(a, c)]
    center = sum(raw) / len(raw)
    return [math.exp(v - center) for v in raw]


def _max_abs_diff(a: Iterable[float], b: Iterable[float]) -> float:
    aa = list(a)
    bb = list(b)
    if len(aa) != len(bb):
        raise ValueError("matching vectors required")
    return max(abs(x - y) for x, y in zip(aa, bb))


def run_proof() -> dict[str, object]:
    cases = []
    synthetic = [
        (
            [1.0, 2.0, 4.0, 3.0, 1.5, 0.7],
            [0.5, 1.0, 2.0, 4.0, 1.0, 0.25],
        ),
        (
            [3.0, 1.0, 1.5, 5.0, 2.0, 0.9, 4.2, 1.7],
            [2.5, 0.8, 1.1, 0.4, 3.2, 1.7, 0.6, 4.0],
        ),
    ]
    for i, (a, d_raw) in enumerate(synthetic, start=1):
        d = normalize_log_shape(d_raw)
        c = camera_shape(a, d)
        recovered = recover_relative_distortion(a, c)
        rescale = recover_relative_distortion(
            a,
            camera_shape(a, [v * 17.3 for v in d_raw]),
        )
        err = _max_abs_diff(recovered, d)
        scale_err = _max_abs_diff(rescale, d)
        cases.append(
            {
                "case": i,
                "bins": len(a),
                "max_abs_recovery_error": err,
                "max_abs_scale_invariance_error": scale_err,
                "pass": err < 1e-12 and scale_err < 1e-12,
            }
        )

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "route_id": "e5-external-activity-anchor-v1",
        "proof_id": "e5-external-activity-anchor-relative-distortion-proof-v1",
        "status": "PASS" if all(x["pass"] for x in cases) else "FAIL",
        "theorem": {
            "observation_model": "C_b = A_b D_b / sum_j(A_j D_j)",
            "normalization": "mean(log D)=0",
            "closed_form": "log D_b = log C_b - log A_b - mean(log C - log A)",
            "identified_quantity": "relative distortion shape only",
        },
        "synthetic_cases": cases,
        "response_boundary": {
            "empirical_values_opened": False,
            "camera_events_opened": False,
            "gps_locations_opened": False,
            "gps_movement_values_opened": False,
            "model_fitting_authorized": False,
        },
        "decision": {
            "A5_structural_identifiability_pass": all(x["pass"] for x in cases),
            "absolute_detection_probability_identified": False,
            "abundance_identified": False,
            "A6_model_freeze_required_before_empirical_values": True,
        },
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = run_proof()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if value["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
