from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from esdm.transfer import (
    ODSPInformationLevel,
    build_odsp_transfer_bundle,
    build_v06a_accessibility_odsp_bundle,
)


def _v06a_result():
    rows = []
    for replicate, (knockout, full) in enumerate(
        ((-2.0, -1.5), (-1.8, -1.6), (-2.2, -1.7))
    ):
        rows.append(
            {
                "replicate": replicate,
                "posterior_means": {},
                "posterior_lows": {},
                "posterior_highs": {},
                "full_heldout_log_score": full,
                "accessibility_knockout_heldout_log_score": knockout,
                "full_divergences": 0,
                "knockout_divergences": 0,
            }
        )
    return {
        "schema": "esdm.v06a.accessibility.v1",
        "status": "PASS",
        "git_sha": "abc123",
        "infrastructure_block": None,
        "replicates": rows,
    }


def test_generic_odsp_adapter_requires_strict_information_filtration():
    records = [{"replicate": 0, "a": -1.0, "b": -0.5}]

    with pytest.raises(ValueError, match="strict nested information levels"):
        build_odsp_transfer_bundle(
            endpoint_id="not-nested",
            levels=(
                ODSPInformationLevel("direct", ("suitability", "accessibility"), "a"),
                ODSPInformationLevel("matched", ("suitability", "accessibility"), "b"),
            ),
            records=records,
            group_field="replicate",
        )


def test_v06a_binding_maps_knockout_to_full_accessibility_filtration():
    bundle = build_v06a_accessibility_odsp_bundle(_v06a_result())

    assert bundle.contract["endpoint_id"] == "esdm_v06a_accessibility_transfer_v1"
    assert bundle.contract["evaluation"]["analysis_mode"] == "descriptive"
    assert bundle.contract["evaluation"]["filtration_frozen_before_outcome_scoring"] is True
    assert bundle.contract["columns"]["block"] is None
    assert bundle.contract["columns"]["population_cluster"] is None

    levels = bundle.contract["levels"]
    assert levels == [
        {
            "name": "suitability_only",
            "information": ["suitability"],
            "score_column": "score__suitability_only",
        },
        {
            "name": "suitability_accessibility",
            "information": ["suitability", "accessibility"],
            "score_column": "score__suitability_accessibility",
        },
    ]

    assert len(bundle.rows) == 3
    assert bundle.rows[0]["group"] == "0"
    assert bundle.rows[0]["score__suitability_only"] == pytest.approx(-2.0)
    assert bundle.rows[0]["score__suitability_accessibility"] == pytest.approx(-1.5)
    assert bundle.manifest["group_semantics"] == "independent known-truth replicate"
    assert bundle.manifest["odsp_top_level_cli"] == "odsp transfer"


def test_adapter_output_is_deterministic_csv_plus_endpoint_contract(tmp_path: Path):
    bundle = build_v06a_accessibility_odsp_bundle(_v06a_result())
    written = bundle.write(tmp_path)

    contract = json.loads(Path(written["contract"]).read_text(encoding="utf-8"))
    manifest = json.loads(Path(written["manifest"]).read_text(encoding="utf-8"))
    with Path(written["scores"]).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert contract["data"] == {"path": "scores.csv", "format": "csv"}
    assert contract["score"]["kind"] == "log"
    assert contract["score"]["common_reference_measure"] is True
    assert contract["evaluation"]["row_independence_if_no_block"] is True
    assert rows[1]["row_id"] == "row-0001"
    assert float(rows[1]["weight"]) == pytest.approx(1.0)
    assert manifest["schema"] == "esdm.odsp_transfer_bundle.v1"
    assert manifest["source_schema"] == "esdm.v06a.accessibility.v1"


def test_v06a_export_rejects_infrastructure_block_and_wrong_schema():
    blocked = _v06a_result()
    blocked["status"] = "INFRASTRUCTURE_BLOCKED"
    blocked["infrastructure_block"] = {"reason": "boom"}
    with pytest.raises(ValueError, match="completed scientific result"):
        build_v06a_accessibility_odsp_bundle(blocked)

    wrong = _v06a_result()
    wrong["schema"] = "esdm.v06c.budget_matched.v1"
    with pytest.raises(ValueError, match="v06a"):
        build_v06a_accessibility_odsp_bundle(wrong)


def test_adapter_does_not_require_odsp_package_dependency():
    bundle = build_v06a_accessibility_odsp_bundle(_v06a_result())
    assert bundle.manifest["odsp_dependency_required_to_export"] is False
