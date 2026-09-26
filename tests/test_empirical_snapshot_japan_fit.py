import hashlib

from esdm.validate.empirical_snapshot_japan_fit import (
    FROZEN_NUM_CHAINS,
    FROZEN_NUM_SAMPLES,
    FROZEN_NUM_WARMUP,
    FROZEN_TARGET_ACCEPT,
    _subset_data,
    _subset_model,
)
from tests.test_empirical_snapshot_japan_camtrapdp import _synthetic_package
from esdm.validate.empirical_snapshot_japan_camtrapdp import (
    build_snapshot_japan_empirical_fixture,
)


def _fixture():
    payload, climate = _synthetic_package()
    return build_snapshot_japan_empirical_fixture(
        camtrapdp_zip=payload,
        climate_payload=climate,
        expected_md5=hashlib.md5(payload).hexdigest(),
    )


def test_empirical_fit_keeps_frozen_r5b_mcmc_profile():
    assert FROZEN_NUM_WARMUP == 300
    assert FROZEN_NUM_SAMPLES == 350
    assert FROZEN_NUM_CHAINS == 2
    assert FROZEN_TARGET_ACCEPT == 0.90


def test_empirical_fit_subsets_training_and_east_holdout_without_leakage():
    fixture = _fixture()
    train, _train_covariates = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout=None,
    )
    heldout, _heldout_covariates = _subset_model(
        fixture,
        fixture.heldout_spaces,
        knockout=None,
    )

    assert len(train.domain.space) == 70
    assert len(heldout.domain.space) == 20

    train_data = _subset_data(fixture, train)
    heldout_data = _subset_data(fixture, heldout)

    assert set(train_data) == {
        "presence_opportunistic",
        "presence_calibrated",
        "annotated",
        "state_calibration",
    }
    assert sum(
        heldout_data["state_calibration"]["sp"]["solitary"].values()
    ) == 0
    assert sum(
        heldout_data["state_calibration"]["sp"]["group"].values()
    ) == 0

    state_calibration = heldout.streams[3]
    assert not any(
        state_calibration.structural_exposure_mask(heldout.domain.keys)
    )


def test_empirical_knockouts_keep_same_observation_streams():
    fixture = _fixture()
    full, _ = _subset_model(fixture, fixture.train_spaces, knockout=None)
    activity, _ = _subset_model(
        fixture, fixture.train_spaces, knockout="activity"
    )
    state, _ = _subset_model(
        fixture, fixture.train_spaces, knockout="state"
    )

    expected = tuple(stream.name for stream in full.streams)
    assert tuple(stream.name for stream in activity.streams) == expected
    assert tuple(stream.name for stream in state.streams) == expected
