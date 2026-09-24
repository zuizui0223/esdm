import importlib.util
import math

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PairEventCount, PresenceOnly
from esdm.process import LinearSuitability, PartnerIntensityEffect


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _fixture(*, source_effort=1.0):
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    effort = EffortField({key: 2.0 for key in grid.keys})
    model = Model(
        grid,
        {
            "focal": (
                LinearSuitability((), "focal_intercept", {}),
                PartnerIntensityEffect(
                    source_species="source",
                    coefficient_parameter="beta_partner",
                    name="partner_effect",
                ),
            ),
            "source": (
                LinearSuitability((), "source_intercept", {}),
            ),
        },
        (
            PresenceOnly(
                "source_records",
                effort=EffortField({key: source_effort for key in grid.keys}),
                informs=frozenset({"suitability"}),
                targets=frozenset({"source"}),
            ),
            PresenceOnly(
                "focal_records",
                effort=EffortField({key: 1.0 for key in grid.keys}),
                informs=frozenset({"suitability", "partner_effect"}),
                targets=frozenset({"focal"}),
            ),
            PairEventCount(
                "events",
                source_species="source",
                target_species="focal",
                effort=effort,
                event_intercept_parameter="event_intercept",
                informs=frozenset({"partner_effect"}),
            ),
        ),
    )
    theta = {
        "source": {"source_intercept": math.log(2.0)},
        "focal": {
            "focal_intercept": math.log(3.0),
            "beta_partner": 0.25,
        },
    }
    theta_obs = {
        "source_records": {},
        "focal_records": {},
        "events": {"event_intercept": math.log(0.5)},
    }
    covariates = {key: {} for key in grid.keys}
    return grid, model, theta, theta_obs, covariates


def test_pair_event_stream_is_pair_specific_and_design_valid():
    _grid, model, _theta, _obs, _covariates = _fixture()
    report = model.check_design()
    events = {stream.name: stream for stream in model.streams}["events"]

    assert events.source_species == "source"
    assert events.target_species == "focal"
    assert events.targets == frozenset({"focal"})
    assert "event_intercept" in events.priors()
    assert ("focal", "partner_effect") in report.informed_processes


def test_pair_event_rate_uses_source_and_target_latent_ecology():
    _grid, model, theta, theta_obs, covariates = _fixture()
    fields = model.latent_fields(theta, covariates)
    events = {stream.name: stream for stream in model.streams}["events"]

    base = events.expected_rates(
        "focal",
        fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
    )

    changed_theta = {
        "source": {"source_intercept": math.log(6.0)},
        "focal": dict(theta["focal"]),
    }
    changed_fields = model.latent_fields(changed_theta, covariates)
    changed = events.expected_rates(
        "focal",
        changed_fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
    )

    assert all(changed[key] > base[key] for key in base)


def test_pair_event_rate_does_not_read_source_observation_effort_directly():
    _grid, low, theta, theta_obs, covariates = _fixture(source_effort=1.0)
    _grid, high, _theta, _obs, _covariates = _fixture(source_effort=100.0)

    low_fields = low.latent_fields(theta, covariates)
    high_fields = high.latent_fields(theta, covariates)
    low_events = {stream.name: stream for stream in low.streams}["events"]
    high_events = {stream.name: stream for stream in high.streams}["events"]

    low_rates = low_events.expected_rates(
        "focal",
        low_fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
    )
    high_rates = high_events.expected_rates(
        "focal",
        high_fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
    )
    assert low_rates == pytest.approx(high_rates)


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_pair_event_scalar_and_array_rates_match():
    import jax.numpy as jnp

    _grid, model, theta, theta_obs, covariates = _fixture()
    scalar_fields = model.latent_fields(theta, covariates)
    array_fields = model.latent_field_arrays(theta, covariates, array_module=jnp)
    events = {stream.name: stream for stream in model.streams}["events"]

    scalar = events.expected_rates(
        "focal",
        scalar_fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
    )
    array = events.expected_rate_array(
        "focal",
        array_fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
        array_module=jnp,
    )

    assert list(map(float, array.values)) == pytest.approx(
        [scalar[key] for key in array.keys]
    )


def test_pair_event_unknown_source_fails_closed_at_model_construction():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    focal = LinearSuitability((), "intercept", {})
    with pytest.raises(ValueError, match="unknown source species"):
        Model(
            grid,
            {"focal": (focal,)},
            (
                PresenceOnly(
                    "focal_records",
                    effort=EffortField({grid.keys[0]: 1.0}),
                    informs=frozenset({"suitability"}),
                    targets=frozenset({"focal"}),
                ),
                PairEventCount(
                    "events",
                    source_species="missing",
                    target_species="focal",
                    effort=EffortField({grid.keys[0]: 1.0}),
                    event_intercept_parameter="event_intercept",
                    informs=frozenset({"suitability"}),
                ),
            ),
        )
