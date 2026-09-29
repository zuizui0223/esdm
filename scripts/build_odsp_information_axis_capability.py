#!/usr/bin/env python3
"""Build deterministic ODSP/eSDM information-axis capability matrix."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build() -> dict:
    contract = _read(ROOT / "ODSP_INFORMATION_AXIS_CAPABILITY_CONTRACT_V1.json")
    registry = _read(ROOT / contract["inputs"]["registry"])
    portfolio = _read(ROOT / contract["inputs"]["validated_portfolio"])
    ledger = _read(ROOT / contract["inputs"]["evidence_ledger"])
    lattice_protocol = _read(ROOT / contract["inputs"]["lattice_protocol"])
    lattice_result = _read(ROOT / contract["inputs"]["lattice_integration"])

    registry_by_id = {
        str(row["source_id"]): row
        for row in registry["sources"]
    }
    portfolio_by_id = {
        str(row["source_id"]): row
        for row in portfolio["items"]
    }

    rows = []
    for declared in contract["axes"]:
        axis_id = str(declared["axis_id"])
        capability = str(declared["capability_class"])
        source_ids = [str(value) for value in declared["source_ids"]]

        if capability == "validated_transfer_value":
            if len(source_ids) != 1:
                raise ValueError(f"{axis_id} validated axis must bind exactly one source")
            source_id = source_ids[0]
            source = registry_by_id[source_id]
            item = portfolio_by_id[source_id]
            if source["status"] != "validated_exportable":
                raise ValueError(f"{axis_id} source is not registry-validated")
            rows.append(
                {
                    "axis_id": axis_id,
                    "capability_class": capability,
                    "source_ids": source_ids,
                    "programme": item["programme"],
                    "endpoint_id": item["endpoint_id"],
                    "lower_level": item["lower_level"],
                    "upper_level": item["upper_level"],
                    "added_information": item["added_information"],
                    "population_mean_gain": item["population_mean_gain"],
                    "mean_interval_lower": item["mean_interval_lower"],
                    "mean_interval_upper": item["mean_interval_upper"],
                    "population_status": item["population_status"],
                    "conservative_mean_value": item["conservative_mean_value"],
                    "positive_group_fraction": item["positive_group_fraction"],
                    "prediction_lower": item["prediction_lower"],
                    "prediction_upper": item["prediction_upper"],
                    "score_kind": item["score_kind"],
                    "score_name": item["score_name"],
                    "score_unit": item["score_unit"],
                    "ordering_relation": item["ordering_relation"],
                    "parallel_family": item["parallel_family"],
                    "validated_integration_receipt": item[
                        "validated_integration_receipt"
                    ],
                    "numeric_transfer_value_authorized": True,
                }
            )
            continue

        if capability == "not_authorized_numeric_transfer":
            source_rows = []
            for source_id in source_ids:
                source = registry_by_id[source_id]
                if source["status"] == "validated_exportable":
                    raise ValueError(
                        f"{axis_id} non-authorized axis contains validated source {source_id}"
                    )
                source_rows.append(
                    {
                        "source_id": source_id,
                        "programme": source["programme"],
                        "registry_status": source["status"],
                        "frozen_result_status": source["frozen_result_status"],
                        "reason": source["reason"],
                    }
                )
            sentinel = ledger.get("interaction_fail_sentinel")
            if axis_id == "interaction":
                if not isinstance(sentinel, dict):
                    raise ValueError("interaction failure sentinel is missing from ledger")
                if sentinel.get("numeric_transfer_value_authorized") is not False:
                    raise ValueError("interaction sentinel must remain non-numeric")
                if sentinel.get("unsupported_not_zero") is not True:
                    raise ValueError("interaction unsupported state must not be converted to zero")
            rows.append(
                {
                    "axis_id": axis_id,
                    "capability_class": capability,
                    "source_ids": source_ids,
                    "sources": source_rows,
                    "numeric_transfer_value": None,
                    "numeric_transfer_value_authorized": False,
                    "unsupported_not_zero": True,
                    "failure_sentinel": sentinel if axis_id == "interaction" else None,
                }
            )
            continue

        if source_ids:
            raise ValueError(
                f"{axis_id} uninstrumented axis must not pretend to have frozen sources"
            )
        rows.append(
            {
                "axis_id": axis_id,
                "capability_class": capability,
                "source_ids": [],
                "numeric_transfer_value": None,
                "numeric_transfer_value_authorized": False,
                "reason": (
                    "no frozen eSDM result currently stores a commensurate absolute held-out "
                    "score contrast for this information axis"
                    if capability == "not_instrumented_no_heldout_score"
                    else "current eSDM process family does not implement this ecological object as a transfer-ready information axis"
                ),
            }
        )

    validated = [
        row for row in rows
        if row["capability_class"] == "validated_transfer_value"
    ]
    unavailable = [
        row for row in rows
        if row["capability_class"] != "validated_transfer_value"
    ]

    axis_source_ids = {
        str(source_id)
        for declared in contract["axes"]
        for source_id in declared["source_ids"]
    }
    unknown_axis_sources = sorted(axis_source_ids - set(registry_by_id))
    if unknown_axis_sources:
        raise ValueError(
            f"capability contract references unknown registry sources: {unknown_axis_sources!r}"
        )

    non_axis_exclusions = []
    for source_id in sorted(set(registry_by_id) - axis_source_ids):
        source = registry_by_id[source_id]
        if source["status"] == "validated_exportable":
            raise ValueError(
                f"validated registry source omitted from capability axes: {source_id}"
            )
        non_axis_exclusions.append(
            {
                "source_id": source_id,
                "programme": source["programme"],
                "registry_status": source["status"],
                "frozen_result_status": source["frozen_result_status"],
                "reason": source["reason"],
                "numeric_transfer_value": None,
                "numeric_transfer_value_authorized": False,
            }
        )

    matrix_source_ids = axis_source_ids | {
        row["source_id"] for row in non_axis_exclusions
    }
    if matrix_source_ids != set(registry_by_id):
        raise ValueError("capability matrix does not account for every registry source")

    protocol_scope = lattice_protocol["current_odsp_scope"]
    if protocol_scope["supported_information_block_counts"] != [2, 3]:
        raise ValueError("lattice protocol supported block counts drifted")
    if protocol_scope["four_or_more_blocks_authorized"] is not False:
        raise ValueError("four-or-more lattice blocks must remain unauthorized")
    if lattice_result["interpretation"]["not_supported"][1] != (
        "retroactive lattice promotion of R5b or any current frozen transfer source"
    ):
        raise ValueError("lattice integration boundary drifted")

    core = {
        "schema": "esdm.odsp_information_axis_capability.v1",
        "contract_id": contract["contract_id"],
        "validated_numeric_axis_count": len(validated),
        "nonvalidated_axis_count": len(unavailable),
        "axes": rows,
        "non_axis_exclusions": non_axis_exclusions,
        "distinctions": contract["distinctions"],
        "lattice_boundary": contract["lattice_boundary"],
        "next_build_rule": contract["next_build_rule"],
        "action_boundary": contract["action_boundary"],
        "evidence_coverage": {
            "registry_source_count": ledger["coverage"]["registry_source_count"],
            "validated_registry_source_count": ledger["coverage"][
                "validated_item_count"
            ],
            "excluded_registry_source_count": ledger["coverage"][
                "excluded_source_count"
            ],
            "every_registry_source_accounted_for": ledger["coverage"][
                "every_registry_source_accounted_for"
            ],
            "matrix_registry_source_count": len(matrix_source_ids),
            "matrix_every_registry_source_accounted_for": (
                matrix_source_ids == set(registry_by_id)
            ),
            "non_axis_exclusion_count": len(non_axis_exclusions),
            "interaction_scientific_fail_retained": (
                ledger["interaction_fail_sentinel"]["frozen_result_status"] == "FAIL"
            ),
        },
    }
    return {**core, "fingerprint": _fingerprint(core)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "validated_numeric_axis_count": result[
                    "validated_numeric_axis_count"
                ],
                "nonvalidated_axis_count": result["nonvalidated_axis_count"],
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
