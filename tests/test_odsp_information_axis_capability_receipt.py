from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "ODSP_INFORMATION_AXIS_CAPABILITY_RECEIPT_V1.json"


def test_capability_receipt_pins_generated_matrix_artifact():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    generation = receipt["generation"]

    assert generation["source_head_sha"] == (
        "5e001d9e34e2b168a413daa5739977899e39641e"
    )
    assert generation["workflow_run_id"] == 36542141025
    assert generation["artifact_id"] == 11020579173
    assert generation["artifact_digest"] == (
        "sha256:f927efb9e5cbf2a515d6629d1bc4ee3641f0fc4cdada7119df13ec1e560101d6"
    )
    assert generation["matrix_sha256"] == (
        "2732b9657b49e738909244705afd1e3f969e03ff0fc817a93ef02952930477aa"
    )
    assert generation["matrix_fingerprint"] == (
        "48be272648fa89a30d0b8d4bd1c62c807c75456a2df21016a7e912e4124800a8"
    )
    assert generation["deterministic_rebuild_authorized"] is True
    assert generation["canonical_snapshot_in_repository"] is False


def test_capability_receipt_has_exact_axis_partition():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    coverage = receipt["coverage"]

    assert coverage["axis_count"] == 7
    assert coverage["validated_numeric_axis_count"] == 4
    assert coverage["nonvalidated_axis_count"] == 3
    assert coverage["validated_axes"] == [
        "accessibility",
        "dynamic_occupancy",
        "activity",
        "latent_state",
    ]
    assert coverage["nonvalidated_axes"] == {
        "interaction": "not_authorized_numeric_transfer",
        "traits": "not_instrumented_no_heldout_score",
        "movement_kernel": "not_instrumented_outside_current_model",
    }
    assert coverage["every_registry_source_accounted_for"] is True


def test_capability_receipt_preserves_fail_closed_boundaries():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["boundaries"]

    assert boundary["interaction_unsupported_not_zero"] is True
    assert boundary["accessibility_is_movement_kernel"] is False
    assert boundary["dynamic_occupancy_is_movement_kernel"] is False
    assert boundary["latent_state_is_trait"] is False
    assert boundary["existing_activity_state_complete_lattice"] is False
    assert boundary["cross_programme_lattice_allowed"] is False
    assert boundary["retrospective_missing_node_reconstruction_allowed"] is False
    assert boundary["new_axis_requires_prospective_absolute_scores"] is True
    assert boundary["authorizes_new_fit"] is False
    assert boundary["authorizes_eog_consumption"] is False
    assert boundary["authorizes_n4_action"] is False
