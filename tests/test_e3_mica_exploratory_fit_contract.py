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
CONTRACT = (
    ROOT / "docs" / "replication" / "E3_MICA_EXPLORATORY_FIT_CONTRACT.json"
)
REDUCED = (
    ROOT / "docs" / "replication" / "E3_MICA_REDUCED_ENDPOINT_CONTRACT.json"
)
WORKFLOW = ROOT / ".github" / "workflows" / "e3-mica-exploratory-fit-once.yml"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_e3_fit_contract_is_bound_to_qualified_reduced_fixture():
    contract = _read(CONTRACT)
    reduced = _read(REDUCED)
    binding = contract["fixture_binding"]
    frozen = reduced["reduced_fixture_capture_result"]

    assert contract["status"] == "FROZEN_PRE_FIT_NOT_AUTHORIZED"
    assert reduced["status"] == "REDUCED_FIXTURE_QUALIFIED_FIT_NOT_AUTHORIZED"
    assert binding["capture_result_sha256"] == frozen["result_sha256"]
    assert (
        binding["fixture_fingerprint_sha256"]
        == frozen["fixture_fingerprint_sha256"]
        == "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
    )
    assert binding["training_spaces"] == 805
    assert binding["heldout_spaces"] == 733
    assert binding["model_stream_names"] == [
        "presence_opportunistic",
        "presence_calibrated",
        "annotated",
    ]
    assert binding["state_calibration_stream_present"] is False
    assert binding["state_calibration_rows_reused"] is False


def test_e3_fit_contract_reuses_frozen_r5b_mcmc_profile():
    contract = _read(CONTRACT)
    mcmc = contract["mcmc"]

    assert mcmc["num_warmup"] == FROZEN_NUM_WARMUP == 300
    assert mcmc["num_samples"] == FROZEN_NUM_SAMPLES == 350
    assert mcmc["num_chains"] == FROZEN_NUM_CHAINS == 2
    assert mcmc["target_accept_probability"] == FROZEN_TARGET_ACCEPT == 0.90
    assert mcmc["rng_seed_full"] == FROZEN_RNG_SEED_FULL == 20260927
    assert mcmc["rng_seed_activity_knockout"] == FROZEN_RNG_SEED_ACTIVITY == 20260928
    assert mcmc["rng_seed_state_knockout"] == FROZEN_RNG_SEED_STATE == 20260929


def test_e3_fit_remains_exploratory_and_requires_pure_authorization():
    contract = _read(CONTRACT)
    interpretation = contract["interpretation"]
    execution = contract["execution"]
    one_shot = contract["one_shot_rule"]
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert interpretation["confirmatory_replication_authorized"] is False
    assert interpretation["independently_calibrated_state_effect_authorized"] is False
    assert interpretation["causal_claim_authorized"] is False
    assert interpretation["e2_rescue_authorized"] is False
    assert execution["exploratory_fit_authorized_now"] is False
    assert one_shot["same_programme_rerun_allowed"] is False
    assert one_shot["threshold_retuning_after_fit_allowed"] is False
    assert one_shot["stream_retuning_after_fit_allowed"] is False
    assert "workflow_dispatch" not in workflow
    assert "E3_MICA_EXPLORATORY_FIT_AUTHORIZED.json" in workflow
