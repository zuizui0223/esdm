from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "ODSP_LATTICE_READY_E2E_RESULT_V1.json"


def _read() -> dict[str, object]:
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_lattice_e2e_result_pins_exact_successful_run():
    result = _read()
    execution = result["execution"]

    assert result["protocol"]["protocol_merge_sha"] == (
        "ced6cd9ba4d50264c1f9d99fd097e4277fddfc3e"
    )
    assert result["protocol"]["integration_merge_sha"] == (
        "af7a32d0f2a52763c0957ca570ff69796beb11cb"
    )
    assert execution["workflow_run_id"] == 36368558802
    assert execution["run_attempt"] == 1
    assert execution["conclusion"] == "success"
    assert execution["artifact_id"] == 10948665791
    assert execution["artifact_digest"] == (
        "sha256:d7695536a66ffec927de627d9f2beeabadd0c4fb0213f49763380b7100748c36"
    )
    assert execution["pinned_odsp_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )


def test_lattice_e2e_point_and_certified_path_status_match():
    result = _read()
    point = result["point_audit"]
    certified = result["certification"]

    assert point["node_count"] == 4
    assert point["edge_count"] == 4
    assert point["full_vs_base_gain_category"] == "generalizing"
    assert point["path_status"] == "order_sensitive_full_transfer"
    assert point["full_transfer_path_count"] == 1
    assert point["total_admissible_path_count"] == 2

    assert certified["all_cells_estimable"] is True
    assert certified["cell_count"] == 8
    assert certified["estimable_cell_count"] == 8
    assert certified["certified_path_status"] == point["path_status"]
    assert certified["robust_full_transfer_path_count"] == 1
    assert certified["total_admissible_path_count"] == 2


def test_lattice_e2e_block_order_robustness_and_shapley_boundary_are_frozen():
    result = _read()
    point = result["point_audit"]
    certified = result["certification"]

    assert point["block_summaries"]["activity"]["order_robust_category"] == (
        "order_robust_generalizing"
    )
    assert point["block_summaries"]["activity"]["shapley_group_gain"] == 0.3
    assert point["block_summaries"]["state"]["order_robust_category"] == (
        "order_sensitive"
    )
    assert abs(point["block_summaries"]["state"]["shapley_group_gain"]) < 1e-15
    assert point["shapley_additivity_error_max_abs"] == 0.0
    assert point["shapley_can_override_edge_failure"] is False

    assert certified["block_summaries"] == {
        "activity": "order_robust_generalizing",
        "state": "order_sensitive",
    }
    assert certified["total_gain_can_override_failed_edge"] is False
    assert certified["shapley_can_override_edge_failure"] is False


def test_lattice_e2e_all_output_hashes_are_frozen():
    hashes = _read()["output_hashes"]

    assert hashes == {
        "lattice_manifest.json": "aec2b29c98c03a26c8ccc9c9122c789322a0160ad400f53d210bfe8b51742fac",
        "lattice_scores.csv": "dd1b69dc07101b4f7af0ce39962459c1bd430d7888bbad6b4945afc75a9ee55f",
        "odsp_lattice_audit.json": "e838c58d44972e03f5be99dc2a93c6c013e0cbc03b7ede86336bbd8f2ec4ea87",
    }


def test_lattice_e2e_remains_synthetic_integration_only():
    interpretation = _read()["interpretation"]

    assert "a new empirical or semi-synthetic ecological result" in interpretation["not_supported"]
    assert "retroactive lattice promotion of R5b or any current frozen transfer source" in interpretation["not_supported"]
    assert "a global cross-programme information ladder" in interpretation["not_supported"]
    assert "four-or-more-block lattice qualification" in interpretation["not_supported"]
    assert "EOG consumption" in interpretation["not_supported"]
    assert "N4 survey action" in interpretation["not_supported"]
