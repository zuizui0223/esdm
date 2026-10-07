#!/usr/bin/env python3
"""Response-free structural identification proof for the external activity-anchor route."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np


def normalize_simplex(x: np.ndarray) -> np.ndarray:
    x=np.asarray(x,dtype=float)
    if x.ndim != 1 or np.any(x <= 0):
        raise ValueError("positive 1D vector required")
    return x/x.sum()


def normalize_log_shape(d: np.ndarray) -> np.ndarray:
    d=np.asarray(d,dtype=float)
    if d.ndim != 1 or np.any(d <= 0):
        raise ValueError("positive 1D vector required")
    logd=np.log(d)
    return np.exp(logd-logd.mean())


def camera_shape(activity: np.ndarray, distortion: np.ndarray) -> np.ndarray:
    a=normalize_simplex(activity)
    d=np.asarray(distortion,dtype=float)
    if a.shape != d.shape or np.any(d <= 0):
        raise ValueError("matching positive vectors required")
    return normalize_simplex(a*d)


def recover_relative_distortion(activity: np.ndarray, camera: np.ndarray) -> np.ndarray:
    a=normalize_simplex(activity)
    c=normalize_simplex(camera)
    if a.shape != c.shape:
        raise ValueError("matching vectors required")
    logd=np.log(c)-np.log(a)
    return np.exp(logd-logd.mean())


def run_proof() -> dict[str,object]:
    cases=[]
    synthetic=[
        (
            np.array([1.0,2.0,4.0,3.0,1.5,0.7]),
            np.array([0.5,1.0,2.0,4.0,1.0,0.25]),
        ),
        (
            np.array([3.0,1.0,1.5,5.0,2.0,0.9,4.2,1.7]),
            np.array([2.5,0.8,1.1,0.4,3.2,1.7,0.6,4.0]),
        ),
    ]
    for i,(a,d_raw) in enumerate(synthetic, start=1):
        d=normalize_log_shape(d_raw)
        c=camera_shape(a,d)
        recovered=recover_relative_distortion(a,c)
        rescale=recover_relative_distortion(a,camera_shape(a,d_raw*17.3))
        err=float(np.max(np.abs(recovered-d)))
        scale_err=float(np.max(np.abs(rescale-d)))
        cases.append({
            "case":i,
            "bins":int(len(a)),
            "max_abs_recovery_error":err,
            "max_abs_scale_invariance_error":scale_err,
            "pass":bool(err < 1e-12 and scale_err < 1e-12),
        })

    return {
        "schema_version":1,
        "programme_id":"E5_INDEPENDENT_ACTIVITY_DETECTION",
        "route_id":"e5-external-activity-anchor-v1",
        "proof_id":"e5-external-activity-anchor-relative-distortion-proof-v1",
        "status":"PASS" if all(x["pass"] for x in cases) else "FAIL",
        "theorem":{
            "observation_model":"C_b = A_b D_b / sum_j(A_j D_j)",
            "normalization":"mean(log D)=0",
            "closed_form":"log D_b = log C_b - log A_b - mean(log C - log A)",
            "identified_quantity":"relative distortion shape only",
        },
        "synthetic_cases":cases,
        "response_boundary":{
            "empirical_values_opened":False,
            "camera_events_opened":False,
            "gps_locations_opened":False,
            "gps_movement_values_opened":False,
            "model_fitting_authorized":False,
        },
        "decision":{
            "A5_structural_identifiability_pass":all(x["pass"] for x in cases),
            "absolute_detection_probability_identified":False,
            "abundance_identified":False,
            "A6_model_freeze_required_before_empirical_values":True,
        },
    }


def main() -> int:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    value=run_proof()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0 if value["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
