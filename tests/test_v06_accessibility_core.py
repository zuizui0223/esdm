import importlib.util

import pytest

from esdm.domain import Grid
from esdm.identify import IdentificationStatus, identify_parameter_from_design
from esdm.model import DesignUninformedError, Model
from esdm.observe import (
    AccessibilityCount,
    AccessiblePresenceOnly,
    EffortField,
    PresenceOnly,
)
from esdm.process import LinearAccessibility, LinearSuitability


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _grid():
    return Grid(space=("a", "b", "c", "d"), doy=(1,), hour=(0,))


def _covariates(grid):
    values = (-1.0, -0.25, 0.5, 1.25)
    return {
        key: {"habitat": values[index], "distance": values[::-1][index]}
        for index, key in enumerate(grid.keys)
    }


def _processes():
    return (
        LinearSuitability(
            covariates=("habitat",),
            intercept_parameter="suitability_intercept",
            coefficient_parameters={"habitat": "beta_habitat"},
        ),
        LinearAccessibility(
            covariates=("distance",),
            intercept_parameter="access_intercept",
            coefficient_parameters={"distance": "beta_distance"},
        ),
    )


def _theta():
    return {
        "sp": {
            "suitability_intercept": 0.3,
            "beta_habitat": 0.7,
            "access_intercept": 0.2,
            "beta_distance": -0.8,
        }
    }


def test_accessibility_probability_is_bounded_and_knockout_is_one():
    grid = _grid()
    cov = _covariates(grid)
    joint = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability", "accessibility"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": _processes()}, (joint,))
    fields = model.latent_fields(_theta(), cov)

    assert all(
        0.0 < fields.accessibility["sp"][key] < 1.0
        for key in grid.keys
    )

    knocked = model.knockout("sp", "accessibility")
    knocked_fields = knocked.latent_fields(
        {
            "sp": {
                "suitability_intercept": 0.3,
                "beta_habitat": 0.7,
            }
        },
        cov,
    )
    assert all(
        knocked_fields.accessibility["sp"][key] == pytest.approx(1.0)
        for key in grid.keys
    )


def test_accessible_presence_multiplies_intensity_by_accessibility():
    grid = _grid()
    cov = _covariates(grid)
    effort = EffortField({key: 2.0 for key in grid.keys})
    stream = AccessiblePresenceOnly(
        "joint",
        effort=effort,
        informs=frozenset({"suitability", "accessibility"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": _processes()}, (stream,))
    fields = model.latent_fields(_theta(), cov)
    rates = stream.expected_rates("sp", fields, covariates=cov)

    import math
    for key in grid.keys:
        expected = (
            math.exp(fields.log_intensity["sp"][key])
            * fields.accessibility["sp"][key]
            * 2.0
        )
        assert rates[key] == pytest.approx(expected)


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_accessibility_scalar_and_array_fields_match():
    import jax.numpy as jnp

    grid = _grid()
    cov = _covariates(grid)
    stream = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability", "accessibility"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": _processes()}, (stream,))

    scalar = model.latent_fields(_theta(), cov)
    array = model.latent_field_arrays(
        _theta(),
        cov,
        array_module=jnp,
    )

    assert list(map(float, array.log_accessibility["sp"].values)) == pytest.approx(
        [scalar.log_accessibility["sp"][key] for key in grid.keys]
    )
    assert list(map(float, array.accessibility["sp"].values)) == pytest.approx(
        [scalar.accessibility["sp"][key] for key in grid.keys]
    )


def test_accessibility_count_does_not_depend_on_suitability():
    grid = _grid()
    cov = _covariates(grid)
    direct = AccessibilityCount(
        "access",
        effort=EffortField({key: 5.0 for key in grid.keys}),
        informs=frozenset({"accessibility"}),
        targets=frozenset({"sp"}),
    )
    joint = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": _processes()}, (joint, direct))

    base = model.latent_fields(_theta(), cov)
    changed_theta = _theta()
    changed_theta["sp"]["suitability_intercept"] = 3.0
    changed = model.latent_fields(changed_theta, cov)

    base_rates = direct.expected_rates("sp", base, covariates=cov)
    changed_rates = direct.expected_rates("sp", changed, covariates=cov)
    assert base_rates == pytest.approx(changed_rates)


def test_standard_presence_only_remains_intensity_only():
    grid = _grid()
    cov = _covariates(grid)
    presence = PresenceOnly(
        "presence",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    direct = AccessibilityCount(
        "access",
        effort=EffortField({key: 5.0 for key in grid.keys}),
        informs=frozenset({"accessibility"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": _processes()}, (presence, direct))

    theta_a = _theta()
    theta_b = _theta()
    theta_b["sp"]["access_intercept"] = -3.0

    fields_a = model.latent_fields(theta_a, cov)
    fields_b = model.latent_fields(theta_b, cov)
    rates_a = presence.expected_rates("sp", fields_a, covariates=cov)
    rates_b = presence.expected_rates("sp", fields_b, covariates=cov)

    assert rates_a == pytest.approx(rates_b)


def test_accessibility_aware_stream_requires_accessibility_process():
    grid = _grid()
    cov = _covariates(grid)
    stream = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability(
                    covariates=("habitat",),
                    intercept_parameter="alpha",
                    coefficient_parameters={"habitat": "beta"},
                ),
            )
        },
        (stream,),
    )
    with pytest.raises(DesignUninformedError, match="log_accessibility"):
        model.check_design()


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_joint_only_intercepts_are_not_identified_but_direct_accessibility_separates():
    grid = _grid()
    cov = {key: {} for key in grid.keys}
    processes = (
        LinearSuitability(
            covariates=(),
            intercept_parameter="suitability_intercept",
            coefficient_parameters={},
        ),
        LinearAccessibility(
            covariates=(),
            intercept_parameter="access_intercept",
            coefficient_parameters={},
        ),
    )
    joint = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 4.0 for key in grid.keys}),
        informs=frozenset({"suitability", "accessibility"}),
        targets=frozenset({"sp"}),
    )
    theta = {
        "sp": {
            "suitability_intercept": 0.5,
            "access_intercept": 0.2,
        }
    }

    joint_only = Model(grid, {"sp": processes}, (joint,))
    refused = identify_parameter_from_design(
        joint_only,
        cov,
        theta=theta,
        theta_obs={"joint": {}},
        target="sp.accessibility.access_intercept",
        method="jax",
    )
    assert refused.status is IdentificationStatus.NOT_IDENTIFIED

    direct = AccessibilityCount(
        "access",
        effort=EffortField({key: 8.0 for key in grid.keys}),
        informs=frozenset({"accessibility"}),
        targets=frozenset({"sp"}),
    )
    informed = Model(grid, {"sp": processes}, (joint, direct))
    accepted = identify_parameter_from_design(
        informed,
        cov,
        theta=theta,
        theta_obs={"joint": {}, "access": {}},
        target="sp.accessibility.access_intercept",
        method="jax",
    )
    assert accepted.status is IdentificationStatus.IDENTIFIED
