from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = (
    ROOT
    / "docs"
    / "replication"
    / "E4_MICA_POSTRESULT_TRANSFER_TAIL_AUDIT.json"
)
RECEIPT = (
    ROOT
    / "docs"
    / "replication"
    / "E4_MICA_POSTRESULT_TRANSFER_TAIL_RECEIPT.json"
)


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_e4_postresult_audit_preserves_frozen_scientific_result_boundary():
    audit = _read(AUDIT)
    receipt = _read(RECEIPT)

    assert audit["status"] == "POSTRESULT_EXPLORATORY_AUDIT"
    assert audit["frozen_result_unchanged"] is True
    assert receipt["status"] == "FROZEN_POSTRESULT_EXPLORATORY_AUDIT"
    boundary = receipt["interpretation_boundary"]
    assert boundary["frozen_e4_result_changed"] is False
    assert boundary["rerun_or_retuning_authorized"] is False
    assert boundary["causal_claim_authorized"] is False
    assert boundary["biological_irrelevance_claim_authorized"] is False


def test_e4_activity_failure_is_tail_concentrated_not_uniform():
    audit = _read(AUDIT)
    activity = audit["score_distribution"]["activity"]
    concentration = audit["score_distribution"]["activity_loss_concentration"]

    assert activity["mean"] == pytest.approx(-0.6390511804117174)
    assert activity["positive_rate"] == pytest.approx(0.8267394270122783)
    assert abs(activity["median"]) < 1e-10
    assert concentration["worst_10_share_of_total_negative_magnitude"] == pytest.approx(
        0.4317718592024589
    )
    assert concentration["worst_50_share_of_total_negative_magnitude"] == pytest.approx(
        0.9083798158499395
    )


def test_e4_activity_holdout_is_outside_training_eastness_support():
    audit = _read(AUDIT)
    support = audit["covariate_support"]

    train_min, train_max = support["training_eastness_z_range"]
    heldout_min, heldout_max = support["heldout_eastness_z_range"]
    assert train_min == pytest.approx(-0.9395454271903178)
    assert train_max == pytest.approx(1.6528810930595796)
    assert heldout_min == pytest.approx(3.1950123639867667)
    assert heldout_max == pytest.approx(8.489597743968037)
    assert heldout_min > train_max
    assert support["heldout_fraction_eastness_z_gt_3"] == 1.0


def test_e4_event_context_activity_is_suppressed_relative_to_knockout_baseline():
    audit = _read(AUDIT)
    diagnostic = audit["activity_transfer_diagnostic"]

    assert diagnostic["event_bearing_heldout_deployments"] == 128
    assert diagnostic["heldout_deployments"] == 733
    assert diagnostic["knockout_baseline_activity_probability"] == pytest.approx(
        0.4380956153696771
    )
    assert diagnostic["event_weighted_posterior_mean_activity_probability"] == pytest.approx(
        0.18502379102459943
    )
    assert diagnostic["event_weighted_activity_to_knockout_ratio"] == pytest.approx(
        0.42233655059174985
    )
    assert diagnostic["corr_activity_gain_labeled_event_count"] < -0.88


def test_e4_transfer_tail_receipt_pins_immutable_audit_artifact():
    receipt = _read(RECEIPT)
    execution = receipt["audit_execution"]

    assert execution["workflow_run_id"] == 36649423614
    assert execution["artifact_id"] == 11069139745
    assert execution["artifact_digest"] == (
        "sha256:e991d5c752c935fdd5c42d6c5e20dbb1349aafdbb7f5491d9054e414dfdcb0f9"
    )
    assert execution["audit_json_sha256"] == (
        "7a5cd9907fc1653017c66e89b57e0088da68a2a2dc69e2cd267819baf5c42373"
    )
