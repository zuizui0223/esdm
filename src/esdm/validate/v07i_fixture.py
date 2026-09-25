"""Disjoint burned-pilot and confirmatory fixtures for v0.7i."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount
from .v07b_fixture import V07B_DIRECT_EFFORT, build_v07b_fixture
from .v07g_fixture import V07G_BASELINE_PLACEMENT, build_v07g_fixture


V07I_PILOT_PLACEMENT = V07G_BASELINE_PLACEMENT
V07I_DIRECT_EFFORT_PER_CONTEXT = float(V07B_DIRECT_EFFORT)
V07I_TOTAL_DIRECT_EFFORT = 4 * V07I_DIRECT_EFFORT_PER_CONTEXT


def _direct_stream(name, domain, placement):
    days = set(int(day) for day in placement)
    return OccupancyCount(
        str(name),
        effort=EffortField({
            key: V07I_DIRECT_EFFORT_PER_CONTEXT
            for key in domain.keys
            if int(key[1]) in days
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )


@dataclass(frozen=True, slots=True)
class V07IPilotFixture:
    source: object
    generator_model: Model
    training_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    pilot_keys: tuple


def build_v07i_pilot_fixture() -> V07IPilotFixture:
    source = build_v07b_fixture()
    joint_generator = next(
        stream for stream in source.generator_model.streams
        if stream.name == "joint"
    )
    joint_training = next(
        stream for stream in source.training_model.streams
        if stream.name == "joint"
    )
    direct = _direct_stream(
        "pilot_calibration",
        source.generator_model.domain,
        V07I_PILOT_PLACEMENT,
    )
    generator = Model(
        source.generator_model.domain,
        source.generator_model.species,
        (joint_generator, direct),
    )
    training = Model(
        source.training_model.domain,
        source.training_model.species,
        (joint_training, direct),
    )
    generator.check_design()
    training.check_design()
    keys = tuple(
        key for key in source.training_model.domain.keys
        if int(key[1]) in set(V07I_PILOT_PLACEMENT)
    )
    return V07IPilotFixture(
        source=source,
        generator_model=generator,
        training_model=training,
        covariates=source.covariates,
        generating_theta=source.generating_theta,
        generating_theta_obs={"joint": {}, "pilot_calibration": {}},
        pilot_keys=keys,
    )


@dataclass(frozen=True, slots=True)
class V07IConfirmFixture:
    source: object
    generator_model: Model
    selected_model: Model
    baseline_model: Model
    scoring_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    selected_placement: tuple[int, ...]
    selected_keys: tuple
    baseline_keys: tuple
    heldout_keys: tuple


def build_v07i_confirm_fixture(selected_placement) -> V07IConfirmFixture:
    source = build_v07b_fixture()
    selected = build_v07g_fixture(selected_placement)
    baseline = build_v07g_fixture(V07G_BASELINE_PLACEMENT)

    joint_generator = next(
        stream for stream in source.generator_model.streams
        if stream.name == "joint"
    )
    joint_training = next(
        stream for stream in source.training_model.streams
        if stream.name == "joint"
    )
    selected_direct = _direct_stream(
        "selected_calibration",
        source.generator_model.domain,
        selected.placement,
    )
    baseline_direct = _direct_stream(
        "baseline_calibration",
        source.generator_model.domain,
        V07G_BASELINE_PLACEMENT,
    )
    generator = Model(
        source.generator_model.domain,
        source.generator_model.species,
        (joint_generator, selected_direct, baseline_direct),
    )
    selected_model = Model(
        source.training_model.domain,
        source.training_model.species,
        (joint_training, selected_direct),
    )
    baseline_model = Model(
        source.training_model.domain,
        source.training_model.species,
        (joint_training, baseline_direct),
    )
    for model in (generator, selected_model, baseline_model):
        model.check_design()

    selected_keys = tuple(
        key for key in source.training_model.domain.keys
        if int(key[1]) in set(selected.placement)
    )
    baseline_keys = tuple(
        key for key in source.training_model.domain.keys
        if int(key[1]) in set(V07G_BASELINE_PLACEMENT)
    )
    return V07IConfirmFixture(
        source=source,
        generator_model=generator,
        selected_model=selected_model,
        baseline_model=baseline_model,
        scoring_model=source.scoring_model,
        covariates=source.covariates,
        generating_theta=source.generating_theta,
        generating_theta_obs={
            "joint": {},
            "selected_calibration": {},
            "baseline_calibration": {},
        },
        selected_placement=selected.placement,
        selected_keys=selected_keys,
        baseline_keys=baseline_keys,
        heldout_keys=source.heldout_keys,
    )
