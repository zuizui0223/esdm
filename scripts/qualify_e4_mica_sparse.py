#!/usr/bin/env python3
"""Qualify exact sparse-domain E4 MICA geometry without fitting."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from esdm.validate.e3_mica_exploratory_fit import build_e3_mica_reduced_fixture
from esdm.validate.e4_mica_sparse import prepare_e4_mica_sparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _report(value):
    return {
        "dense_context_count": value.dense_context_count,
        "compact_context_count": value.compact_context_count,
        "reduction_factor": value.reduction_factor,
        "retained_keys_sha256": value.retained_keys_sha256,
        "exposed_contexts_by_stream": dict(value.exposed_contexts_by_stream),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = _read("E4_MICA_SPARSE_NUTS_CONTRACT.json")
    e2 = _read("E2_MICA_FULL_RESPONSE_CONTRACT.json")
    e3 = _read("E3_MICA_EXPLORATORY_CONTRACT.json")
    preflight = _read("E3_MICA_EXPLORATORY_PREFLIGHT_RESULT.json")
    reduced = _read("E3_MICA_REDUCED_ENDPOINT_CONTRACT.json")

    if contract["status"] != "FROZEN_PRE_OUTCOME_IMPLEMENTATION_ONLY":
        raise SystemExit("E4 sparse contract is not frozen pre-outcome")
    if contract["qualification_before_empirical_fit"]["empirical_fit_authorized_now"] is not False:
        raise SystemExit("E4 qualification branch may not authorize empirical fitting")
    if _sha256(args.archive) != contract["immutable_source"]["source_archive_sha256"]:
        raise SystemExit("E4 source archive sha256 drift")

    capture_bytes = args.capture.read_bytes()
    capture = json.loads(capture_bytes)
    if capture.get("status") != "E3_REDUCED_FIXTURE_QUALIFIED":
        raise SystemExit("E4 requires the qualified E3 reduced capture receipt")
    observed_capture_fp = capture["fixture_diagnostics"]["fixture_fingerprint_sha256"]
    expected_fp = contract["immutable_source"]["e3_fixture_fingerprint_sha256"]
    if observed_capture_fp != expected_fp:
        raise SystemExit("E4 captured fixture fingerprint drift")

    climate = json.loads(args.climate.read_text(encoding="utf-8"))
    fixture, diagnostics = build_e3_mica_reduced_fixture(
        source_archive=args.archive,
        climate_payload=climate,
        e2_full_contract=e2,
        e3_contract=e3,
        preflight_receipt=preflight,
        reduced_contract=reduced,
    )
    if diagnostics["fixture_fingerprint_sha256"] != expected_fp:
        raise SystemExit("E4 rebuilt fixture fingerprint drift")

    prepared = prepare_e4_mica_sparse(fixture)
    observed = {
        "training": _report(prepared.training_compaction),
        "heldout": _report(prepared.heldout_compaction),
    }
    frozen = contract["exact_compaction"]
    for section in ("training", "heldout"):
        expected = frozen[section]
        for field in (
            "dense_context_count",
            "compact_context_count",
            "retained_keys_sha256",
            "exposed_contexts_by_stream",
        ):
            if observed[section][field] != expected[field]:
                raise SystemExit(
                    f"E4 {section} {field} drift: "
                    f"{observed[section][field]!r} != {expected[field]!r}"
                )

    result = {
        "schema_version": 1,
        "programme_id": contract["programme_id"],
        "result_id": "e4-mica-sparse-qualification-v1",
        "status": "E4_SPARSE_QUALIFIED",
        "source_archive_sha256": _sha256(args.archive),
        "capture_result_sha256": _sha256(args.capture),
        "fixture_fingerprint_sha256": diagnostics["fixture_fingerprint_sha256"],
        "compaction": observed,
        "scientific_result": {
            "model_fits": 0,
            "heldout_scores": 0,
            "activity_gain": None,
            "state_gain": None,
        },
        "decision": {
            "empirical_fit_authorized_from_qualification": False,
            "same_qualification_rerun_allowed": False,
            "laplace_backend_authorized": False,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "training_compact_contexts": observed["training"]["compact_context_count"],
        "heldout_compact_contexts": observed["heldout"]["compact_context_count"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
