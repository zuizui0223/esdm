from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT = (
    ROOT / "docs" / "replication"
    / "E4_MICA_POSTRESULT_CROSS_TAXON_DIEL_SUPPLEMENT.json"
)
RECEIPT = (
    ROOT / "docs" / "replication"
    / "E4_MICA_POSTRESULT_CROSS_TAXON_DIEL_RECEIPT.json"
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_cross_taxon_diel_supplement_is_postresult_negative_control_only():
    value = _read(SUPPLEMENT)
    boundary = value["analysis_boundary"]

    assert value["status"] == "POSTRESULT_EXPLORATORY_SUPPLEMENT"
    assert value["supplement_id"] == "e4-mica-postresult-cross-taxon-diel-v1"
    assert boundary["post_outcome"] is True
    assert boundary["new_model_fit"] is False
    assert boundary["posterior_refit"] is False
    assert boundary["retuning"] is False
    assert boundary["backend_switch"] is False
    assert boundary["claim_promotion"] is False
    assert boundary["cross_taxon_diagnostic_only"] is True


def test_cross_taxon_diel_shift_is_shared_but_not_universal():
    value = _read(SUPPLEMENT)
    summary = value["summary"]

    assert summary["eligible_binomial_species_count"] == 8
    assert summary["negative_log_ratio_shift_count"] == 7
    assert summary["nonfocal_eligible_species_count"] == 7
    assert summary["nonfocal_negative_log_ratio_shift_count"] == 6
    assert summary["median_rate_ratio_multiplier"] == pytest.approx(
        0.11488735557505754
    )
    assert summary["nonfocal_median_rate_ratio_multiplier"] == pytest.approx(
        0.11458592509534794
    )

    taxa = {row["scientificName"]: row for row in value["taxa"]}
    assert taxa["Rattus norvegicus"]["direction"] == "higher"
    assert taxa["Anas platyrhynchos"]["direction"] == "lower"
    assert taxa["Ardea cinerea"]["direction"] == "lower"


def test_muskrat_shift_is_negative_but_not_the_most_extreme():
    value = _read(SUPPLEMENT)
    summary = value["summary"]

    assert summary["focal_species"] == "Ondatra zibethicus"
    assert summary["focal_log_rate_ratio_change"] == pytest.approx(
        -1.4179217994234241
    )
    assert summary["focal_negative_shift_rank_most_negative_is_1"] == 6

    focal = next(row for row in value["taxa"] if row["focal"])
    assert focal["training_night_day_rate_ratio"] == pytest.approx(
        12.239191071168491
    )
    assert focal["heldout_D_night_day_rate_ratio"] == pytest.approx(
        2.9645385457310307
    )


def test_cross_taxon_receipt_pins_immutable_artifact_and_forbids_causal_promotion():
    value = _read(RECEIPT)
    execution = value["audit_execution"]

    assert value["status"] == "FROZEN_POSTRESULT_EXPLORATORY_SUPPLEMENT"
    assert execution["workflow_run_id"] == 36656041321
    assert execution["head_sha"] == (
        "7c1a24e8bb3b132d3882cad9e792e609c14eb383"
    )
    assert execution["artifact_id"] == 11073080845
    assert execution["artifact_digest"] == (
        "sha256:7ec2d4f86fba244b1f6cca2a0c6f3f40621d9fb31beb69e743d9592b1f5063db"
    )
    assert execution["supplement_json_sha256"] == (
        "73f0275996a549ee408e9b3e637c3c894313b4fa7ac801fa7da7106e4837a545"
    )

    boundary = value["interpretation_boundary"]
    assert boundary["cross_taxon_negative_control_only"] is True
    assert boundary["causal_camera_detection_claim"] is False
    assert boundary["causal_observer_or_annotation_claim"] is False
    assert boundary["universal_taxon_shift_claim"] is False
    assert boundary["causal_muskrat_behavior_claim"] is False
    assert boundary["frozen_e4_decision_changed"] is False
    assert boundary["rerun_or_retuning_authorized"] is False
