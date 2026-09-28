#!/usr/bin/env python3
"""Preflight the frozen E3 MICA exploratory metadata repair without fitting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from esdm.validate.e2_mica_response_blind import qualify_e2_mica_archive
from esdm.validate.e3_mica_exploratory import (
    audit_nonpositive_deployment_durations,
    sanitize_archive_by_deployment_ids,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "docs" / "replication" / "E3_MICA_EXPLORATORY_CONTRACT.json"


def _assert_equal(name: str, observed, expected) -> None:
    if observed != expected:
        raise ValueError(f"{name} mismatch: {observed!r} != {expected!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    frozen = contract["frozen_metadata_audit"]
    source = contract["source_boundary"]

    audit = audit_nonpositive_deployment_durations(args.archive)
    _assert_equal("source archive sha256", audit["source_sha256"], source["source_archive_sha256"])
    _assert_equal("deployment row count", audit["deployment_row_count"], frozen["deployment_rows"])
    _assert_equal(
        "nonpositive duration count",
        audit["nonpositive_duration_count"],
        frozen["nonpositive_duration_deployments"],
    )
    _assert_equal("negative duration count", audit["negative_duration_count"], 0)
    _assert_equal(
        "excluded deployment IDs",
        audit["excluded_deployment_ids"],
        frozen["excluded_deployment_ids"],
    )
    _assert_equal(
        "excluded deployment ID hash",
        audit["excluded_deployment_ids_sha256"],
        frozen["excluded_deployment_ids_sha256"],
    )

    with tempfile.TemporaryDirectory(prefix="esdm-e3-") as tmp:
        sanitized = Path(tmp) / "mica-e3-sanitized.zip"
        filtering = sanitize_archive_by_deployment_ids(
            args.archive,
            sanitized,
            excluded_deployment_ids=set(audit["excluded_deployment_ids"]),
        )
        qualified = qualify_e2_mica_archive(sanitized)

    geometry = qualified["geometry"]
    fingerprints = qualified["fingerprints"]
    roles = qualified["roles"]

    _assert_equal("retained deployment count", geometry["deployment_count"], frozen["e3_retained_deployments"])
    _assert_equal("training deployment count", geometry["training_deployment_count"], frozen["e3_expected_training_deployments"])
    _assert_equal("heldout deployment count", geometry["heldout_deployment_count"], frozen["e3_expected_heldout_deployments"])
    _assert_equal("max training longitude", geometry["max_training_longitude"], frozen["e3_max_training_longitude"])
    _assert_equal("min heldout longitude", geometry["min_heldout_longitude"], frozen["e3_min_heldout_longitude"])
    _assert_equal("longitude gap", geometry["longitude_gap"], frozen["e3_longitude_gap"])
    _assert_equal("training IDs hash", fingerprints["training_ids_sha256"], frozen["e3_training_ids_sha256"])
    _assert_equal("heldout IDs hash", fingerprints["heldout_ids_sha256"], frozen["e3_heldout_ids_sha256"])
    _assert_equal(
        "training role map hash",
        fingerprints["training_role_map_sha256"],
        frozen["e3_training_role_map_sha256"],
    )
    _assert_equal("manifest hash", fingerprints["manifest_sha256"], frozen["e3_manifest_sha256"])
    _assert_equal(
        "removed deployment rows",
        filtering["removed_deployment_rows"],
        frozen["nonpositive_duration_deployments"],
    )
    _assert_equal(
        "removed observation rows",
        filtering["removed_observation_rows"],
        frozen["observation_rows_removed_by_excluded_deployment_id"],
    )
    _assert_equal(
        "total original observation rows",
        filtering["removed_observation_rows"] + filtering["retained_observation_rows"],
        frozen["observations_rows_total_in_immutable_capture"],
    )

    result = {
        "schema_version": 1,
        "result_id": "e3-mica-exploratory-preflight-v1",
        "status": "E3_PREFLIGHT_PASS",
        "programme_id": contract["programme_id"],
        "source_archive_sha256": audit["source_sha256"],
        "metadata_audit": audit,
        "filtering": filtering,
        "qualified_geometry": geometry,
        "qualified_roles": roles,
        "qualified_fingerprints": fingerprints,
        "decision": {
            "preflight_passed": True,
            "exploratory_fit_authorized_by_this_receipt": False,
            "requires_separate_pure_authorization_marker": True,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "training": geometry["training_deployment_count"],
        "heldout": geometry["heldout_deployment_count"],
        "removed_observation_rows": filtering["removed_observation_rows"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
