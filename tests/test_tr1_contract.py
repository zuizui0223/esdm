from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "TR1_TRAIT_TRANSFER_CONTRACT_V1.json"


def _read():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_tr1_contract_is_frozen_before_outcome_and_targets_unseen_taxa():
    contract = _read()

    assert contract["status"] == "pre_outcome_frozen"
    assert contract["data_generating_process"]["taxon_count"] == 30
    assert contract["data_generating_process"]["training_taxon_count"] == 20
    assert contract["data_generating_process"]["heldout_taxon_count"] == 10
    assert contract["heldout_design"]["heldout_taxa_never_used_for_fitting"] is True
    assert contract["learners"]["taxon_identity_included"] is False
    assert contract["data_generating_process"]["taxon_random_effect"] == 0.0


def test_tr1_contract_removes_environment_proxy_route():
    contract = _read()
    dgp = contract["data_generating_process"]

    assert dgp["environment_grid_count"] == 41
    assert "shared identically by every taxon" in dgp["environment_grid"]
    assert "cannot earn predictive gain merely by proxying" in dgp[
        "reason_common_environment_grid"
    ]


def test_tr1_contract_requires_absolute_scores_and_strict_trait_filtration():
    contract = _read()
    odsp = contract["odsp_ready_result"]

    assert odsp["positive_world_absolute_scores_required"] == [
        "environment_only_heldout_log_score",
        "environment_trait_heldout_log_score",
    ]
    assert odsp["information_filtration"] == [
        {
            "name": "environment_only",
            "information": ["environment"],
            "score_field": "environment_only_heldout_log_score",
        },
        {
            "name": "environment_traits",
            "information": ["environment", "traits"],
            "score_field": "environment_trait_heldout_log_score",
        },
    ]
    assert odsp["odsp_changes_tr1_promotion"] is False


def test_tr1_positive_and_null_gates_are_both_required():
    contract = _read()

    assert contract["positive_world_gate"] == {
        "mean_full_minus_environment_gain_minimum": 0.03,
        "positive_gain_rate_minimum": 0.75,
        "absolute_mean_trait_coefficient_bias_maximum": 0.15,
    }
    assert contract["null_world_specificity_gate"][
        "material_gain_threshold"
    ] == 0.01
    assert contract["null_world_specificity_gate"][
        "material_gain_count_maximum"
    ] == 8
    assert contract["null_world_specificity_gate"]["mean_gain_maximum"] == 0.005
    assert contract["decision"]["pass_requires_all_positive_and_null_gates"] is True
    assert contract["decision"]["outcome_access_before_contract_merge_allowed"] is False


def test_tr1_positive_threshold_is_calibrated_to_known_truth_oracle():
    contract = _read()
    oracle = contract["oracle_calibration"]

    assert oracle["positive_world_expected_trait_information_gain"] == (
        0.06306753955889005
    )
    assert oracle["null_world_expected_trait_information_gain"] == 0.0
    assert 0.45 < oracle["positive_gate_mean_gain_fraction_of_oracle"] < 0.50
