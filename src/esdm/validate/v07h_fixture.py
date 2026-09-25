"""Expected-direct-record matched placement control for v0.7h."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount
from .v07g_fixture import (
    V07G_BASELINE_PLACEMENT,
    V07G_SELECTED_PLACEMENT,
    build_v07g_validation_fixture,
)


V07H_BASELINE_EFFORT_PER_CONTEXT = 500.0
V07H_BASELINE_EXPECTED_DIRECT_COUNT = 931.25
V07H_SELECTED_EFFORT_PER_CONTEXT = 369.15453700836173
V07H_SELECTED_TOTAL_EFFORT = 4 * V07H_SELECTED_EFFORT_PER_CONTEXT
V07H_BASELINE_TOTAL_EFFORT = 4 * V07H_BASELINE_EFFORT_PER_CONTEXT


@dataclass(frozen=True, slots=True)
class V07HFixture:
    source: object
    selected_model: Model
    baseline_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    selected_keys: tuple
    baseline_keys: tuple


def _replace_direct_stream(source_model, placement, effort_per_context):
    days = set(int(day) for day in placement)
    direct = OccupancyCount(
        "occupancy_calibration",
        effort=EffortField({
            key: float(effort_per_context)
            for key in source_model.domain.keys
            if int(key[1]) in days
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )
    joint = next(
        stream for stream in source_model.streams
        if stream.name == "joint"
    )
    model = Model(
        source_model.domain,
        source_model.species,
        (joint, direct),
    )
    model.check_design()
    keys = tuple(
        key for key in source_model.domain.keys
        if int(key[1]) in days
    )
    return model, keys


def build_v07h_fixture() -> V07HFixture:
    source = build_v07g_validation_fixture()

    selected_model, selected_keys = _replace_direct_stream(
        source.optimized_model,
        V07G_SELECTED_PLACEMENT,
        V07H_SELECTED_EFFORT_PER_CONTEXT,
    )
    baseline_model, baseline_keys = _replace_direct_stream(
        source.baseline_model,
        V07G_BASELINE_PLACEMENT,
        V07H_BASELINE_EFFORT_PER_CONTEXT,
    )

    return V07HFixture(
        source=source,
        selected_model=selected_model,
        baseline_model=baseline_model,
        covariates=source.covariates,
        generating_theta=source.generating_theta,
        generating_theta_obs=source.generating_theta_obs,
        selected_keys=selected_keys,
        baseline_keys=baseline_keys,
    )


def expected_direct_count(model, fixture) -> float:
    stream = next(
        stream for stream in model.streams
        if stream.name == "occupancy_calibration"
    )
    fields = model.latent_fields(
        fixture.generating_theta,
        fixture.covariates,
    )
    rates = stream.expected_rates(
        "sp",
        fields,
        theta_obs={},
        covariates=fixture.covariates,
    )
    return sum(float(value) for value in rates.values())
