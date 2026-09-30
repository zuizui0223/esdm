from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = (
    ROOT / "docs" / "replication" / "E4_MICA_SPARSE_FROZEN_RESULT.json"
)


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_e4_terminal_result_is_bound_to_the_one_authorized_run():
    value = _read()
    execution = value["execution"]

    assert value["status"] == "E4_SPARSE_EMPIRICAL_RESULT"
    assert value["programme_id"] == "E4_MICA_SPARSE_NUTS"
    assert execution["workflow_run_id"] == 36622802225
    assert execution["run_attempt"] == 1
    assert execution["authorization_head_sha"] == (
        "8a1bd87733637494c89e03e389faf6b1c64605a0"
    )
    assert execution["artifact_id"] == 11059622869
    assert execution["artifact_digest"] == (
        "sha256:da72e996014d988c9ee55e99ac6cebf5662030fa35abcf9203d3f83cf84c5bfe"
    )
    assert execution["result_json_sha256"] == (
        "34124094e6c25db04465cc1ff869af5813326729e6fd3b658a0921c45bc6f3e2"
    )


def test_e4_terminal_result_passes_sampling_and_score_identities():
    value = _read()
    scores = value["summary"]["scores"]

    assert value["decision"]["sampling_gate_passed"] is True
    assert value["summary"]["divergences"]["total"] == 0
    assert value["summary"]["heldout_row_count"] == 733
    assert value["summary"]["max_abs_aggregate_identity_error"] == 0.0
    assert math.isclose(
        scores["activity_gain"],
        scores["full_heldout_log_score"]
        - scores["activity_knockout_heldout_log_score"],
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert math.isclose(
        scores["state_gain"],
        scores["full_heldout_log_score"]
        - scores["state_knockout_heldout_log_score"],
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert scores["activity_gain"] < 0.0
    assert scores["state_gain"] > 0.0
    assert value["decision"]["activity_predictive_support_descriptive"] is False
    assert value["decision"]["state_predictive_support_descriptive"] is True


def test_e4_terminal_result_preserves_exact_sparse_geometry_and_closes_rescue():
    value = _read()
    compaction = value["summary"]["compaction"]

    assert compaction["training"]["dense_context_count"] == 615020
    assert compaction["training"]["compact_context_count"] == 11531
    assert compaction["training"]["retained_keys_sha256"] == (
        "41bd70aa1f913bcb1c988f6c5cdae3441ed978d4ee0f6791bcfc497290710646"
    )
    assert compaction["heldout"]["dense_context_count"] == 560012
    assert compaction["heldout"]["compact_context_count"] == 10168
    assert compaction["heldout"]["retained_keys_sha256"] == (
        "0ed3fb9e96b1323a4290b7cb92621d219e317b8b916201a1b2665db4a272b1d9"
    )

    terminal = value["terminal_rule"]
    assert terminal["same_programme_rerun_allowed"] is False
    assert terminal["post_result_threshold_retuning_allowed"] is False
    assert terminal["post_result_stream_retuning_allowed"] is False
    assert terminal["backend_switch_within_e4_allowed"] is False
    assert value["interpretation_boundary"]["laplace_or_inla_authorized"] is False
    assert value["interpretation_boundary"]["confirmatory_replication_claim"] is False
    assert value["interpretation_boundary"]["causal_claim"] is False
