from __future__ import annotations

import math

import pytest

from esdm.domain import Grid, StateSpace
from esdm.model import Model, compact_model_by_structural_exposure
from esdm.observe import (
    EffortField,
    KnownDetection,
    PresenceOnly,
    StateAnnotatedCount,
)
from esdm.process import LinearActivity, LinearState, LinearSuitability
from esdm.validate.empirical_snapshot_japan_camtrapdp import MaskedLogLinearEffort


STATES = StateSpace(("solitary", "group"))


def _fixture():
    grid = Grid(
        space=("a", "b", "c"),
        doy=(1, 8, 15),
        hour=(3, 9),
    )
    keys = grid.keys
    covariates = {}
    for index, key in enumerate(keys):
        covariates[key] = {
            "precip": (index - 7.0) / 5.0,
            "east": (-1.0, 0.0, 1.0)[("a", "b", "c").index(key[0])],
            "season_sin": math.sin(index / 3.0),
            "season_cos": math.cos(index / 3.0),
            "diurnal_sin": -0.5 if key[2] == 3 else 0.5,
            "diurnal_cos": 0.5 if key[2] == 3 else -0.5,
        }

    processes = (
        LinearSuitability(
            covariates=("precip", "east", "season_sin"),
            intercept_parameter="intercept",
            coefficient_parameters={
                "precip": "beta_precip",
                "east": "beta_east",
                "season_sin": "beta_season",
            },
        ),
        LinearActivity(
            covariates=("precip", "east", "season_cos", "diurnal_cos"),
            intercept_parameter="activity_intercept",
            coefficient_parameters={
                "precip": "activity_beta_precip",
                "east": "activity_beta_east",
                "season_cos": "activity_beta_season",
                "diurnal_cos": "activity_beta_diurnal",
            },
        ),
        LinearState(
            state_space=STATES,
            reference_state="solitary",
            covariates=("precip", "east", "season_sin", "diurnal_sin"),
            intercept_parameters={"group": "alpha_group"},
            coefficient_parameters={
                "group": {
                    "precip": "beta_group_precip",
                    "east": "beta_group_east",
                    "season_sin": "beta_group_season",
                    "diurnal_sin": "beta_group_diurnal",
                }
            },
        ),
    )

    opportunistic = frozenset((keys[0], keys[3]))
    calibrated = {keys[7]: 0.75, keys[8]: 1.0}
    annotated = {keys[12]: 0.5, keys[13]: 1.0, keys[17]: 0.25}
    streams = (
        PresenceOnly(
            name="presence_opportunistic",
            effort=MaskedLogLinearEffort(
                exposed_keys=opportunistic,
                covariate="season_sin",
                coefficient_parameter="gamma_presence_season",
            ),
            detection_probability=1.0,
            informs=frozenset({"suitability"}),
            targets=frozenset({"sp"}),
        ),
        PresenceOnly(
            name="presence_calibrated",
            effort=EffortField(calibrated),
            detection_probability=1.0,
            informs=frozenset({"suitability"}),
            targets=frozenset({"sp"}),
        ),
        StateAnnotatedCount(
            name="annotated",
            state_space=STATES,
            effort=EffortField(annotated),
            detection=KnownDetection(probability=1.0),
            informs=frozenset({"activity", "state"}),
            targets=frozenset({"sp"}),
        ),
    )
    model = Model(grid, {"sp": processes}, streams)
    data = {
        "presence_opportunistic": {"sp": {keys[0]: 1}},
        "presence_calibrated": {"sp": {keys[8]: 2}},
        "annotated": {
            "sp": {
                "solitary": {keys[12]: 1, keys[17]: 1},
                "group": {keys[13]: 2},
            }
        },
    }
    return model, covariates, data, {
        keys[0], keys[3], keys[7], keys[8], keys[12], keys[13], keys[17]
    }


def _theta():
    return {
        "sp": {
            "intercept": -0.3,
            "beta_precip": 0.2,
            "beta_east": -0.15,
            "beta_season": 0.1,
            "activity_intercept": 0.25,
            "activity_beta_precip": -0.1,
            "activity_beta_east": 0.2,
            "activity_beta_season": 0.15,
            "activity_beta_diurnal": -0.2,
            "alpha_group": -1.1,
            "beta_group_precip": 0.3,
            "beta_group_east": -0.25,
            "beta_group_season": 0.2,
            "beta_group_diurnal": 0.1,
        }
    }


def test_structural_compaction_is_exact_for_e3_like_likelihood():
    model, covariates, data, expected = _fixture()
    compact, compact_covariates, compact_data, report = (
        compact_model_by_structural_exposure(model, covariates, data)
    )
    theta_obs = {
        "presence_opportunistic": {"gamma_presence_season": 0.35},
        "presence_calibrated": {},
        "annotated": {},
    }

    dense_ll = model.log_likelihood(
        data,
        _theta(),
        covariates,
        theta_obs=theta_obs,
    )
    compact_ll = compact.log_likelihood(
        compact_data,
        _theta(),
        compact_covariates,
        theta_obs=theta_obs,
    )

    assert set(compact.domain.keys) == expected
    assert report.dense_context_count == 18
    assert report.compact_context_count == 7
    assert report.reduction_factor == pytest.approx(18 / 7)
    assert compact_ll == pytest.approx(dense_ll, abs=1e-12, rel=0.0)


def test_structural_compaction_fails_closed_on_nonzero_unexposed_data():
    model, covariates, data, _expected = _fixture()
    impossible = model.domain.keys[5]
    data["presence_calibrated"]["sp"][impossible] = 1

    with pytest.raises(ValueError, match="outside structural exposure"):
        compact_model_by_structural_exposure(model, covariates, data)
