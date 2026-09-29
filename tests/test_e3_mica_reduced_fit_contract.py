from __future__ import annotations

import json
from pathlib import Path

from esdm.validate.e2_mica_fit import (
    FROZEN_NUM_CHAINS,
    FROZEN_NUM_SAMPLES,
    FROZEN_NUM_WARMUP,
    FROZEN_RNG_SEED_ACTIVITY,
    FROZEN_RNG_SEED_FULL,
    FROZEN_RNG_SEED_STATE,
    FROZEN_TARGET_ACCEPT,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E3_MICA_REDUCED_FIT_CONTRACT.json"


def _read():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_e3_reduced_fit_contract_is_frozen_but_not_authorized():
    contract = _read()

    assert contract["programme_id"] == "E3_MICA_EXP"
    assert contract["contract_id"] == "e3-mica-reduced-exploratory-fit-v1"
    assert contract["status"] == "FROZEN_FIT_NOT_AUTHORIZED"
    assert contract["execution"]["fit_authorized_now"] is False
    assert contract["execution"]["one_authorized_run"] is True
    assert contract["execution"]["workflow_dispatch_enabled"] is False
    assert contract["execution"]["same_programme_rerun_allowed"] is False
    assert contract["execution"]["authorization_requires_new_pure_marker_commit"] is True


def test_e3_reduced_fit_is_bound_to_qualified_capture():
    contract = _read()
    source = contract["source"]

    assert source["immutable_e2_capture_workflow_run_id"] == 36369531079
    assert source["immutable_e2_capture_artifact_id"] == 10947948379
    assert source["e3_capture_workflow_run_id"] == 36399428007
    assert source["e3_capture_artifact_id"] == 10958744325
    assert source["e3_capture_result_sha256"] == (
        "77f0286f1cc09ff03e0e53222c445316b961eef6ec0d5ceb505445dcff7d43be"
    )
    assert source["required_capture_status"] == "E3_REDUCED_FIXTURE_QUALIFIED"
    assert source["required_fixture_fingerprint_sha256"] == (
        "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
    )


def test_e3_reduced_fit_reuses_exact_e2_r5b_mcmc_profile():
    fit = _read()["fit"]

    assert fit["fits"] == ["full", "activity_knockout", "state_knockout"]
    assert fit["num_warmup"] == FROZEN_NUM_WARMUP == 300
    assert fit["num_samples"] == FROZEN_NUM_SAMPLES == 350
    assert fit["num_chains"] == FROZEN_NUM_CHAINS == 2
    assert fit["target_accept_probability"] == FROZEN_TARGET_ACCEPT == 0.90
    assert fit["rng_seed_full"] == FROZEN_RNG_SEED_FULL == 20260927
    assert fit["rng_seed_activity_knockout"] == FROZEN_RNG_SEED_ACTIVITY == 20260928
    assert fit["rng_seed_state_knockout"] == FROZEN_RNG_SEED_STATE == 20260929


def test_e3_reduced_fit_requires_absolute_scores_and_no_effect_threshold():
    contract = _read()
    outputs = contract["outputs"]
    decision = contract["decision"]

    assert outputs["heldout_row_count"] == 733
    assert outputs["row_level_absolute_scores_required"] is True
    assert outputs["equal_weight_row_mean_must_match_aggregate_score"] is True
    assert outputs["absolute_scores_required"] == [
        "full_heldout_log_score",
        "activity_knockout_heldout_log_score",
        "state_knockout_heldout_log_score",
    ]

    assert decision["minimum_effect_size_threshold"] is None
    assert decision["confirmatory_replication_claim"] is False
    assert decision["e2_rescue"] is False
    assert decision["causal_claim"] is False
    assert decision["parameter_recovery_claim"] is False


def test_e3_reduced_fit_keeps_state_calibration_removed():
    fixture = _read()["fixture"]

    assert fixture["training_deployments"] == 805
    assert fixture["heldout_deployments"] == 733
    assert fixture["state_calibration_stream_present"] is False
    assert fixture["state_calibration_rows_reused"] is False
    assert fixture["training_roles_reassigned"] is False


def test_e3_reduced_fit_odsp_boundary_is_post_fit_descriptive_only():
    odsp = _read()["odsp_readiness"]

    assert odsp["allowed_after_completed_fit"] is True
    assert odsp["result_role"] == "exploratory_real_data_transfer_audit"
    assert odsp["absolute_score_reconstruction_from_gains_allowed"] is False
    assert odsp["odsp_result_cannot_change_e3_descriptive_fit_result"] is True
