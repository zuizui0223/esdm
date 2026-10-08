#!/usr/bin/env python3
"""Response-free gauge counterexample for uncalibrated paired camera streams.

Two camera-member event rates do not determine a common latent diel activity
curve and two time-varying detection curves unless additional observation
information breaks the multiplicative gauge freedom.
"""
from __future__ import annotations

import json
import math
from pathlib import Path


def expected_camera_rate(
    activity: list[float], detection: list[float], effort: list[float]
) -> list[float]:
    if not (len(activity) == len(detection) == len(effort)) or not activity:
        raise ValueError("nonempty aligned vectors required")
    if any(not math.isfinite(x) or x <= 0 for x in activity + effort):
        raise ValueError("activity/effort must be finite positive")
    if any(not math.isfinite(p) or p <= 0 or p > 1 for p in detection):
        raise ValueError("detection must be in (0,1]")
    return [a*p*e for a,p,e in zip(activity,detection,effort)]


def gauge_transform(
    activity: list[float],
    detection: list[float],
    multiplier: list[float],
) -> tuple[list[float],list[float]]:
    if not (len(activity) == len(detection) == len(multiplier)):
        raise ValueError("aligned vectors required")
    if any(not math.isfinite(h) or h <= 0 for h in multiplier):
        raise ValueError("positive multiplier required")
    activity_new=[a*h for a,h in zip(activity,multiplier)]
    detection_new=[p/h for p,h in zip(detection,multiplier)]
    if any(p>1 for p in detection_new):
        raise ValueError("transformed probabilities exceed 1")
    return activity_new,detection_new


def normalized_shape(values: list[float]) -> list[float]:
    return [v/sum(values) for v in values]


def run_proof() -> dict:
    activity=[1.0,3.0,2.0,4.0,1.5,2.5]
    detector_1=[0.18,0.32,0.25,0.52,0.23,0.19]
    detector_2=[0.35,0.27,0.48,0.36,0.29,0.37]
    e1=[1.0,1.0,0.7,1.0,0.85,1.0]
    e2=[0.8,1.0,1.0,0.9,1.0,1.0]
    h=[1.4,1.1,2.0,1.3,1.9,1.2]

    old=[expected_camera_rate(activity,p,e) for p,e in
         ((detector_1,e1),(detector_2,e2))]
    an,p1n=gauge_transform(activity,detector_1,h)
    an2,p2n=gauge_transform(activity,detector_2,h)
    assert an==an2
    new=[expected_camera_rate(an,p,e) for p,e in ((p1n,e1),(p2n,e2))]
    max_rate_error=max(abs(old[j][i]-new[j][i])
                       for j in range(2) for i in range(len(activity)))
    original_shape=normalized_shape(activity)
    changed_shape=normalized_shape(an)
    max_activity_shape_change=max(abs(x-y) for x,y in
                                  zip(original_shape,changed_shape))
    max_camera_ratio_error=max(abs(
        detector_1[i]/detector_2[i] - p1n[i]/p2n[i]
    ) for i in range(len(activity)))
    passed=(max_rate_error<1e-12
            and max_camera_ratio_error<1e-12
            and max_activity_shape_change>1e-3)
    return {
        "schema_version":1,
        "proof_id":"e5-rhode-island-uncalibrated-paired-product-gauge-v1",
        "status":"PASS_NONIDENTIFICATION_WITNESS" if passed else "FAIL",
        "synthetic_time_bins":len(activity),
        "max_observation_rate_error":max_rate_error,
        "max_relative_detection_ratio_error":max_camera_ratio_error,
        "max_normalized_activity_shape_difference":max_activity_shape_change,
        "interpretation":"identical observed event rates and relative camera detection ratios admit different latent activity shapes",
        "provenance":{"all_values_synthetic":True,
                      "focal_response_rows_opened":False,
                      "empirical_model_fit":False},
        "G4_pass_authorized":False,
    }


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    value=run_proof()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",
                        encoding="utf-8")
    return 0 if value["status"]=="PASS_NONIDENTIFICATION_WITNESS" else 1


if __name__=="__main__":
    raise SystemExit(main())
