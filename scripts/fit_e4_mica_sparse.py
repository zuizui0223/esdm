#!/usr/bin/env python3
"""Run the one authorized E4 exact-sparse MICA fit."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from esdm.validate.e3_mica_exploratory_fit import build_e3_mica_reduced_fixture
from esdm.validate.e4_mica_sparse import fit_e4_mica_sparse_nuts


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _compaction_payload(report):
    return {
        "dense_context_count": int(report.dense_context_count),
        "compact_context_count": int(report.compact_context_count),
        "reduction_factor": float(report.reduction_factor),
        "retained_keys_sha256": str(report.retained_keys_sha256),
        "exposed_contexts_by_stream": dict(report.exposed_contexts_by_stream),
    }


def _base_result(contract, qualification_sha256):
    return {
        "schema_version": 1,
        "result_id": contract["outputs"]["result_id"],
        "programme_id": contract["programme_id"],
        "endpoint_id": contract["scientific_endpoint"]["endpoint_id"],
        "fit_contract_id": contract["contract_id"],
        "status": "E4_SPARSE_EXECUTION_STARTED",
        "qualification": {
            "workflow_run_id": contract["qualification"]["workflow_run_id"],
            "artifact_id": contract["qualification"]["artifact_id"],
            "result_sha256": qualification_sha256,
            "fixture_fingerprint_sha256": contract["qualification"][
                "required_fixture_fingerprint_sha256"
            ],
        },
        "decision": {
            "sampling_gate_passed": None,
            "activity_predictive_support_descriptive": None,
            "state_predictive_support_descriptive": None,
            "minimum_effect_size_threshold": None,
            "confirmatory_replication_claim": False,
            "e3_rescue": False,
            "causal_claim_authorized": False,
            "parameter_recovery_claim_authorized": False,
            "same_programme_rerun_allowed": False,
            "post_outcome_retuning_allowed": False,
        },
        "response_boundary": {
            "biological_response_already_consumed_under_e2": True,
            "new_external_response_gets": 0,
            "model_fits": 0,
            "heldout_scores": 0,
            "state_calibration_stream_present_in_fit": False,
        },
        "inference_boundary": {
            "backend": "NumPyro NUTS",
            "exact_sparse_compaction": True,
            "posterior_target_changed": False,
            "approximation_introduced": False,
            "laplace_or_inla_used": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    fit_contract = _read("E4_MICA_SPARSE_FIT_CONTRACT.json")
    sparse_contract = _read("E4_MICA_SPARSE_NUTS_CONTRACT.json")
    e2 = _read("E2_MICA_FULL_RESPONSE_CONTRACT.json")
    e3 = _read("E3_MICA_EXPLORATORY_CONTRACT.json")
    preflight = _read("E3_MICA_EXPLORATORY_PREFLIGHT_RESULT.json")
    reduced = _read("E3_MICA_REDUCED_ENDPOINT_CONTRACT.json")

    if fit_contract["status"] != "FROZEN_FIT_NOT_AUTHORIZED":
        raise SystemExit("E4 fit contract is not frozen pre-authorization")
    if fit_contract["execution"]["fit_authorized_now"] is not False:
        raise SystemExit("E4 implementation branch may not self-authorize fitting")
    if _sha256(args.archive) != fit_contract["immutable_source"]["source_archive_sha256"]:
        raise SystemExit("E4 source archive sha256 drift")
    if _sha256(args.capture) != fit_contract["immutable_source"][
        "e3_reduced_capture_result_sha256"
    ]:
        raise SystemExit("E4 reduced capture result sha256 drift")

    qualification_sha256 = _sha256(args.qualification)
    if qualification_sha256 != fit_contract["qualification"]["result_sha256"]:
        raise SystemExit("E4 qualification result sha256 drift")
    qualification = json.loads(args.qualification.read_text(encoding="utf-8"))
    if qualification.get("status") != fit_contract["qualification"]["required_status"]:
        raise SystemExit("E4 qualification status drift")
    if qualification.get("fixture_fingerprint_sha256") != fit_contract[
        "qualification"
    ]["required_fixture_fingerprint_sha256"]:
        raise SystemExit("E4 qualification fixture fingerprint drift")

    frozen = fit_contract["exact_compaction"]
    observed = qualification["compaction"]
    expected_fields = {
        ("training", "dense_context_count"): frozen["training_dense_contexts"],
        ("training", "compact_context_count"): frozen["training_compact_contexts"],
        ("training", "retained_keys_sha256"): frozen[
            "training_retained_keys_sha256"
        ],
        ("heldout", "dense_context_count"): frozen["heldout_dense_contexts"],
        ("heldout", "compact_context_count"): frozen["heldout_compact_contexts"],
        ("heldout", "retained_keys_sha256"): frozen[
            "heldout_retained_keys_sha256"
        ],
    }
    for (section, field), expected in expected_fields.items():
        if observed[section][field] != expected:
            raise SystemExit(
                f"E4 qualification compaction drift: {section}.{field}"
            )

    # Write a durable receipt before any expensive fixture materialization or MCMC.
    # If the runner is externally killed, this file remains uploadable.
    result = _base_result(fit_contract, qualification_sha256)
    _write(args.out, result)

    try:
        climate = json.loads(args.climate.read_text(encoding="utf-8"))
        fixture, diagnostics = build_e3_mica_reduced_fixture(
            source_archive=args.archive,
            climate_payload=climate,
            e2_full_contract=e2,
            e3_contract=e3,
            preflight_receipt=preflight,
            reduced_contract=reduced,
        )
        expected_fp = fit_contract["qualification"][
            "required_fixture_fingerprint_sha256"
        ]
        if diagnostics["fixture_fingerprint_sha256"] != expected_fp:
            raise ValueError("E4 rebuilt fixture fingerprint drift")

        fitted = fit_e4_mica_sparse_nuts(fixture, progress_bar=False)
        scientific = fitted.scientific_result
        scores = {
            "full_heldout_log_score": scientific.full_heldout_log_score,
            "activity_knockout_heldout_log_score": (
                scientific.activity_knockout_heldout_log_score
            ),
            "state_knockout_heldout_log_score": (
                scientific.state_knockout_heldout_log_score
            ),
            "activity_gain": scientific.activity_gain,
            "state_gain": scientific.state_gain,
        }
        if not all(math.isfinite(float(value)) for value in scores.values()):
            raise ValueError("E4 fit produced non-finite score/gain")

        rows = list(scientific.heldout_deployment_scores)
        if len(rows) != int(fit_contract["outputs"]["heldout_row_count"]):
            raise ValueError("E4 heldout deployment row count drift")

        compaction = {
            "training": _compaction_payload(fitted.training_compaction),
            "heldout": _compaction_payload(fitted.heldout_compaction),
        }
        for (section, field), expected in expected_fields.items():
            if compaction[section][field] != expected:
                raise ValueError(
                    f"E4 fitted compaction drift: {section}.{field}"
                )

        result.update({
            "status": (
                "E4_SPARSE_EMPIRICAL_RESULT"
                if scientific.sampling_passed
                else "E4_SPARSE_SAMPLING_STOP"
            ),
            "fixture_fingerprint_sha256": expected_fp,
            "compaction": compaction,
            "scores": scores,
            "divergences": {
                "full": scientific.full_divergences,
                "activity_knockout": scientific.activity_knockout_divergences,
                "state_knockout": scientific.state_knockout_divergences,
                "total": scientific.total_divergences,
            },
            "parameter_summaries": dict(scientific.parameter_summaries),
            "heldout_deployment_scores": rows,
            "odsp_serialization": {
                "row_count": len(rows),
                "row_unit": fit_contract["outputs"]["heldout_row_unit"],
                "absolute_scores_serialized": True,
                "gain_only_serialization": False,
                "same_scored_cells_across_models": True,
            },
        })
        result["decision"].update({
            "sampling_gate_passed": bool(scientific.sampling_passed),
            "activity_predictive_support_descriptive": bool(
                scientific.sampling_passed and scientific.activity_gain > 0.0
            ),
            "state_predictive_support_descriptive": bool(
                scientific.sampling_passed and scientific.state_gain > 0.0
            ),
        })
        result["response_boundary"].update({
            "model_fits": 3,
            "heldout_scores": 3,
        })
        _write(args.out, result)
        return 0 if scientific.sampling_passed else 2
    except Exception as exc:
        result.update({
            "status": "E4_SPARSE_EXECUTION_STOP",
            "reason": f"{type(exc).__name__}: {exc}",
        })
        result["decision"]["sampling_gate_passed"] = False
        _write(args.out, result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
