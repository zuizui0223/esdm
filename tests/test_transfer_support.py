"""Unit tests never open external biological response or refit E4."""

import json
from pathlib import Path

import pytest

from esdm.transfer.support import audit_process_transfer_support


ROOT = Path(__file__).resolve().parents[1]


def call(**extra):
    options = dict(
        training_covariate_bounds={"eastness_z": (-1.0, 2.0), "precip_z": (-2.0, 2.0)},
        target_covariate_bounds={"eastness_z": (0.0, 1.0), "precip_z": (-1.0, 0.5)},
        training_observation_domains={"original-a"},
        target_observation_domains={"original-a"},
        independently_calibrated_observation=True,
    )
    options.update(extra)
    return audit_process_transfer_support(**options)


def test_qualified_means_input_support_only_not_predictive_gain():
    result = call()
    assert result.status == "INPUT_SUPPORT_ONLY"
    assert result.input_support_qualified
    assert not result.reasons


def test_closed_bounds_allow_equal_endpoints():
    assert call(target_covariate_bounds={"eastness_z": (-1, 2), "precip_z": (-2, 2)}).input_support_qualified


def test_extrapolation_blocks_even_if_other_evidence_passes():
    result = call(target_covariate_bounds={"eastness_z": (2, 3), "precip_z": (-1, 1)})
    assert result.status == "TRANSFER_INPUT_NOT_QUALIFIED"
    assert result.covariates_outside_training == ("eastness_z",)
    assert "TARGET_COVARIATE_EXTRAPOLATION" in result.reasons


def test_missing_target_feature_is_not_evaluable():
    result = call(target_covariate_bounds={"eastness_z": (0, 1)})
    assert result.status == "NOT_EVALUABLE"
    assert result.covariates_without_target_bounds == ("precip_z",)


def test_unseen_source_cannot_silently_count_as_replication():
    result = call(target_observation_domains={"original-a", "new-b"})
    assert result.previously_unseen_source_domains == ("new-b",)
    assert not result.input_support_qualified


def test_calibration_must_be_independent_and_explicit():
    result = call(independently_calibrated_observation=False)
    assert "INDEPENDENT_OBSERVATION_CALIBRATION_NOT_SUPPLIED" in result.reasons
    with pytest.raises(ValueError):
        call(independently_calibrated_observation=None)


@pytest.mark.parametrize("bad", [(0, float("inf")), (2, 1), (float("nan"), 0), (1,), (False, 1), ("wrong", 2)])
def test_bad_bounds_fail_closed(bad):
    with pytest.raises(ValueError):
        call(training_covariate_bounds={"eastness_z": bad})


@pytest.mark.parametrize("bad", ["source", set(), {""}, {3}])
def test_bad_source_identities_fail_closed(bad):
    with pytest.raises(ValueError):
        call(training_observation_domains=bad)


def test_archived_e4_real_covariate_support_and_domain_shift_are_not_claimed_as_new_fit():
    audit = json.loads((ROOT / "docs/replication/E4_MICA_POSTRESULT_TRANSFER_TAIL_AUDIT.json").read_text())
    shift = json.loads((ROOT / "docs/replication/E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json").read_text())
    training = {"eastness_z": audit["covariate_support"]["training_eastness_z_range"],
                "precip_z": audit["covariate_support"]["training_precip_z_range"]}
    target = {"eastness_z": audit["covariate_support"]["heldout_eastness_z_range"],
              "precip_z": audit["covariate_support"]["heldout_precip_z_range"]}
    before = {k for k, v in shift["source_stratum_shift"]["training_state_annotated_deployments_by_prefix"].items() if v > 0}
    after = {k for k, v in shift["source_stratum_shift"]["heldout_deployments_by_prefix"].items() if v > 0}
    result = audit_process_transfer_support(
        training_covariate_bounds=training,
        target_covariate_bounds=target,
        training_observation_domains=before,
        target_observation_domains=after,
        independently_calibrated_observation=False,
    )
    assert result.status == "TRANSFER_INPUT_NOT_QUALIFIED"
    assert "eastness_z" in result.covariates_outside_training
    assert result.previously_unseen_source_domains == ("D", "NL")
    assert "INDEPENDENT_OBSERVATION_CALIBRATION_NOT_SUPPLIED" in result.reasons
