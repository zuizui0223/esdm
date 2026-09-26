import json
from pathlib import Path

from esdm.validate.empirical_snapshot_japan_fit import (
    FROZEN_NUM_CHAINS,
    FROZEN_NUM_SAMPLES,
    FROZEN_NUM_WARMUP,
    FROZEN_TARGET_ACCEPT,
)


def _contract():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "empirical"
            / "SNAPSHOT_JAPAN_CAMTRAPDP_FINAL_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )


def test_final_empirical_contract_is_frozen_before_response():
    contract = _contract()

    assert contract["status"] == "FROZEN_BEFORE_FIRST_CAMTRAPDP_RESPONSE_OPEN"
    assert contract["source"]["zenodo_record"] == 15030971
    assert contract["source"]["file_name"] == "oo_1246258.zip"
    assert contract["source"]["md5"] == "742f186013ef3b60e9754df73e5269de"
    assert contract["focal_endpoint"]["species"] == "Cervus nippon"
    assert contract["focal_endpoint"]["state_space"] == ["solitary", "group"]
    assert contract["spatial_contract"]["expected_training_count"] == 70
    assert contract["spatial_contract"]["expected_heldout_count"] == 20
    assert contract["training_stream_partition"]["direct_state_calibration_heldout_exposure"] == 0
    assert contract["response_capture"]["model_fits_in_capture_stage"] == 0
    assert contract["response_capture"]["heldout_scores_in_capture_stage"] == 0
    assert contract["one_open_rule"]["candidate_switch_after_consumed_response"] is False


def test_final_empirical_contract_uses_frozen_r5b_mcmc_profile():
    contract = _contract()

    assert contract["fit"]["num_warmup"] == FROZEN_NUM_WARMUP == 300
    assert contract["fit"]["num_samples"] == FROZEN_NUM_SAMPLES == 350
    assert contract["fit"]["num_chains"] == FROZEN_NUM_CHAINS == 2
    assert contract["fit"]["target_accept_probability"] == FROZEN_TARGET_ACCEPT == 0.90


def test_final_empirical_contract_pins_response_blind_climate():
    contract = _contract()

    assert contract["climate_input"]["workflow_run_id"] == 36271741095
    assert contract["climate_input"]["artifact_id"] == 10916116137
    assert contract["climate_input"]["camera_climate_sha256"] == (
        "abecf035ebf7862df52a61be6ea34e89086961b67891359776582da08ab27ea4"
    )
