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
    assert execution["workflow_run_id"] == 36657253598
    assert execution["head_sha"] == (
        "d63fbce6a7606e186c4905bfa5d2d76a6c32bbc1"
    )
    assert execution["artifact_id"] == 11072868461
    assert execution["artifact_digest"] == (
        "sha256:7405b6a5bf00a3ecace784115cddcfdbe26cbde1de296acc6dbff866873499f5"
    )
    assert execution["supplement_json_sha256"] == (
        "ccbedd9894dc30590166a4bccd3ff3c30645951bc2d69d353fb89614443b402a"
    )

    boundary = value["interpretation_boundary"]
    assert boundary["cross_taxon_negative_control_only"] is True
    assert boundary["causal_camera_detection_claim"] is False
    assert boundary["causal_observer_or_annotation_claim"] is False
    assert boundary["universal_taxon_shift_claim"] is False
    assert boundary["causal_muskrat_behavior_claim"] is False
    assert boundary["frozen_e4_decision_changed"] is False
    assert boundary["rerun_or_retuning_authorized"] is False
