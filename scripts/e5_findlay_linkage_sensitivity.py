#!/usr/bin/env python3
"""Retrospective aggregate-only Findlay cohort-linkage sensitivity.

Never opens source event CSVs, joins unknown passages, or refits the frozen run.
"""
import argparse
import json
from pathlib import Path


def calculate(receipt):
    assert receipt["receipt_id"] == "e5-findlay-known-pass-stage-terminal-receipt-v1"
    assert receipt["provenance"]["workflow_run_id"] == 37770893387
    assert receipt["quality_limits"]["FOX_composite_conditioned_on_unverified_row_identity"] is True
    cells = {(x["species"], x["distance_bin"]): x
             for x in receipt["stage_cells"]}
    near = cells[("FOX", "near_le_1m")]
    far = cells[("FOX", "far_gt_3m")]
    required = ("cctv_reference_passes", "triggered_reference_passes",
                "registration_eligible_triggered_rows", "registered_images")
    assert tuple(near[k] for k in required) == (88,55,55,19)
    assert tuple(far[k] for k in required) == (175,47,47,27)
    badger = cells[("BADGER", "far_gt_3m")]
    assert tuple(badger[k] for k in required) == (82,16,15,8)
    trace = []
    for k in range(7):
        n_low, n_high = max(0,19-k), min(55,19+k)
        f_low, f_high = max(0,27-k), min(47,27+k)
        trace.append({
            "assumed_max_substitutions_in_each_bin": k,
            "near_registered_bounds": [n_low,n_high],
            "far_registered_bounds": [f_low,f_high],
            "minimum_near_minus_far_total": n_low/88 - f_high/175,
            "minimum_far_minus_near_conditional": f_low/47 - n_high/55,
        })
    first_total = next(x["assumed_max_substitutions_in_each_bin"] for x in trace
                       if x["minimum_near_minus_far_total"] <= 0)
    first_conditional = next(x["assumed_max_substitutions_in_each_bin"] for x in trace
                            if x["minimum_far_minus_near_conditional"] <= 0)
    assert (first_total, first_conditional) == (4,6)
    return {
        "schema_version": 1,
        "route_id": "e5-findlay-passage-linkage-sensitivity-postoutcome",
        "status": "EXPLORATORY_ONLY_NOT_IDENTITY_VALIDATION",
        "upstream_run_id": 37770893387,
        "upstream_result_sha256": receipt["provenance"]["result_json_sha256"],
        "assumption": "At most k hypothetical substitutions of arbitrary binary registered-pass outcomes in EACH FOX bin, preserving each frozen CCTV pass and trigger denominator",
        "actual_mismatch_k_measured": False,
        "upper_bound_on_actual_k_established": False,
        "FOX_thresholds": {
            "first_k_per_bin_erasing_near_greater_than_far_composite": first_total,
            "first_k_per_bin_erasing_far_greater_than_near_registration": first_conditional,
        },
        "FOX_trace": trace,
        "BADGER_far": {
            "reference_passes": 82,
            "reference_triggers": 16,
            "registration_eligible_rows": 15,
            "observed_registered": 8,
            "bounds_if_exactly_one_missing_and_remaining_rows_matched": [8/82,9/82],
            "subset_assumption_verified": False,
            "composite_identified": False,
        },
        "boundaries": {
            "source_event_CSVs_opened": False,
            "additional_empirical_run": False,
            "original_one_shot_rerun": False,
            "passage_level_identity_proven": False,
            "statistical_CI_calculated": False,
            "original_result_reclassified": False,
            "diel_detection_identified": False,
            "geographic_transfer_supported": False,
            "original_E5_G4_passed": False,
            "original_E5_qualified": 0,
            "original_E5_screened": 17
        }
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    v = calculate(json.loads(args.receipt.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8")
