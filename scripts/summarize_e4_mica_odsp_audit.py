#!/usr/bin/env python3
"""Summarize E4 MICA ODSP block audits without changing the frozen E4 result."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


EXPECTED_GROUP = "MICA_MUSKRAT"
EXPECTED_BLOCKS = 733
EXPECTED_ACTIVITY_GAIN = -0.6390511804117178
EXPECTED_STATE_GAIN = 0.008390925023042506
GAIN_TOLERANCE = 1e-12


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _one(name: str, receipt: dict, *, expected_gain: float) -> dict:
    certification = receipt["certified_result"]["certification"]
    if len(certification["steps"]) != 1:
        raise ValueError(f"{name} audit must contain exactly one transfer step")
    step = certification["steps"][0]
    if len(step["groups"]) != 1:
        raise ValueError(f"{name} audit must contain exactly one endpoint group")
    cell = step["groups"][0]
    if cell["group"] != EXPECTED_GROUP:
        raise ValueError(f"{name} endpoint group drifted")
    if int(cell["block_count"]) != EXPECTED_BLOCKS:
        raise ValueError(f"{name} block count drifted")
    if int(cell["row_count"]) != EXPECTED_BLOCKS:
        raise ValueError(f"{name} row count drifted")
    if cell["estimable"] is not True:
        raise ValueError(f"{name} within-endpoint block audit must be estimable")

    observed_gain = float(cell["mean_gain"])
    if not math.isclose(
        observed_gain,
        float(expected_gain),
        rel_tol=0.0,
        abs_tol=GAIN_TOLERANCE,
    ):
        raise ValueError(
            f"{name} ODSP point gain drifted: {observed_gain} != {expected_gain}"
        )

    population = receipt["population_result"]
    if int(population["group_count"]) != 1:
        raise ValueError(f"{name} population_result must reflect one endpoint group")
    if population["familywise_confirmatory_claim"] is not False:
        raise ValueError(f"{name} population_result must remain descriptive")

    return {
        "endpoint_id": receipt["endpoint_id"],
        "lower_level": step["lower_level"],
        "upper_level": step["upper_level"],
        "point_mean_gain": observed_gain,
        "frozen_e4_point_gain": float(expected_gain),
        "point_gain_identity_passed": True,
        "certified_category": step["category"],
        "certified_group_status": cell["status"],
        "certified_lower_bound": float(cell["lower_bound"]),
        "certified_upper_bound": float(cell["upper_bound"]),
        "certified_transfer_ceiling": certification["certified_transfer_ceiling"],
        "point_transfer_ceiling": certification["point_transfer_ceiling"],
        "row_count": int(cell["row_count"]),
        "block_count": int(cell["block_count"]),
        "population_result_serialized": True,
        "population_result_scientific_use_authorized": False,
    }


def summarize(source_receipt: dict, activity_receipt: dict, state_receipt: dict) -> dict:
    if source_receipt.get("result_id") != "e4-mica-exact-sparse-frozen-result-v1":
        raise ValueError("unexpected E4 frozen source receipt")
    if source_receipt.get("programme_id") != "E4_MICA_SPARSE_NUTS":
        raise ValueError("unexpected E4 programme")
    if source_receipt.get("status") != "E4_SPARSE_EMPIRICAL_RESULT":
        raise ValueError("ODSP audit requires E4_SPARSE_EMPIRICAL_RESULT")
    if source_receipt["decision"].get("sampling_gate_passed") is not True:
        raise ValueError("ODSP audit requires E4 sampling gate PASS")

    frozen_scores = source_receipt["summary"]["scores"]
    if not math.isclose(
        float(frozen_scores["activity_gain"]),
        EXPECTED_ACTIVITY_GAIN,
        rel_tol=0.0,
        abs_tol=GAIN_TOLERANCE,
    ):
        raise ValueError("frozen E4 activity gain drifted")
    if not math.isclose(
        float(frozen_scores["state_gain"]),
        EXPECTED_STATE_GAIN,
        rel_tol=0.0,
        abs_tol=GAIN_TOLERANCE,
    ):
        raise ValueError("frozen E4 state gain drifted")

    return {
        "schema_version": 1,
        "audit_id": "e4-mica-odsp-parallel-audit-result-v1",
        "audit_status": "POSTRESULT_DESCRIPTIVE_AUDIT",
        "source": {
            "programme_id": source_receipt["programme_id"],
            "result_id": source_receipt["result_id"],
            "status": source_receipt["status"],
            "workflow_run_id": source_receipt["execution"]["workflow_run_id"],
            "artifact_id": source_receipt["execution"]["artifact_id"],
            "result_json_sha256": source_receipt["execution"]["result_json_sha256"],
        },
        "activity": _one(
            "activity",
            activity_receipt,
            expected_gain=EXPECTED_ACTIVITY_GAIN,
        ),
        "state": _one(
            "state",
            state_receipt,
            expected_gain=EXPECTED_STATE_GAIN,
        ),
        "frozen_decision": {
            "activity_predictive_support_descriptive": source_receipt["decision"][
                "activity_predictive_support_descriptive"
            ],
            "state_predictive_support_descriptive": source_receipt["decision"][
                "state_predictive_support_descriptive"
            ],
            "odsp_may_change_decision": False,
        },
        "boundary": {
            "parallel_not_ordered": True,
            "combined_three_level_filtration_authorized": False,
            "odsp_lattice_authorized": False,
            "population_superpopulation_interpretation_authorized": False,
            "n3_transfer_value_handoff_authorized": False,
            "confirmatory_replication": False,
            "causal_activity": False,
            "causal_state": False,
            "e4_rerun_or_retuning_authorized": False,
            "backend_switch_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--activity-receipt", type=Path, required=True)
    parser.add_argument("--state-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = summarize(
        _read(args.source_receipt),
        _read(args.activity_receipt),
        _read(args.state_receipt),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "activity_gain": result["activity"]["point_mean_gain"],
        "activity_category": result["activity"]["certified_category"],
        "state_gain": result["state"]["point_mean_gain"],
        "state_category": result["state"]["certified_category"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
