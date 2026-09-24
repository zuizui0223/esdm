import importlib.util
import math

import pytest

from esdm.domain import Grid
from esdm.model import DesignUninformedError, Model
from esdm.observe import EffortField, InteractionEventCount, KnownDetection, PresenceOnly
from esdm.process import LinearSuitability, PartnerIntensityEffect


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _model():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    event = InteractionEventCount(
        "events",
        source_species="source",
        effort=EffortField({key: 0.5 for key in grid.keys}),
        detection=KnownDetection(0.9),
        event_logit_parameter="event_logit",
        informs=frozenset({"partner_effect"}),
        targets=frozenset({"focal"}),
    )
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
                effort=EffortField({key: 1.0 for key in grid.keys}),
                informs=frozenset({"suitability"}),
                targets=frozenset({"source"}),
            ),
            PresenceOnly(
                "focal_records",
                effort=EffortField({key: 1.0 for key in grid.keys}),
                informs=frozenset({"suitability", "partner_effect"}),
                targets=frozenset({"focal"}),
            ),
            event,
        ),
    )
    theta = {
        "source": {"source_intercept": math.log(2.0)},
        "focal": {
            "focal_intercept": math.log(3.0),
            "beta_partner": 0.0,
        },
    }
    theta_obs = {
        "source_records": {},
        "focal_records": {},
        "events": {"event_logit": 0.0},
    }
    covariates = {key: {} for key in grid.keys}
    return grid, model, theta, theta_obs, covariates


def test_interaction_event_rate_uses_paired_latent_abundance():
    grid, model, theta, theta_obs, covariates = _model()
    fields = model.latent_fields(theta, covariates)
    stream = {stream.name: stream for stream in model.streams}["events"]

    block = stream.observation_blocks(
        "focal",
        fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
    )[0]

    # source abundance 2 × focal abundance 3 × p(event)=0.5
    # × effort 0.5 × detection 0.9 = 1.35
    assert tuple(block.rates) == pytest.approx((1.35, 1.35))
    assert block.name == "events.source->focal"


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_interaction_event_scalar_and_array_rates_match():
    import jax.numpy as jnp

    _grid, model, theta, theta_obs, covariates = _model()
    stream = {stream.name: stream for stream in model.streams}["events"]

    scalar_fields = model.latent_fields(theta, covariates)
    scalar = stream.observation_blocks(
        "focal",
        scalar_fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
    )[0]

    array_fields = model.latent_field_arrays(
        theta,
        covariates,
        array_module=jnp,
    )
    array = stream.observation_blocks(
        "focal",
        array_fields,
        theta_obs=theta_obs["events"],
        covariates=covariates,
        array_module=jnp,
    )[0]

    assert list(map(float, array.rates)) == pytest.approx(scalar.rates)


def test_interaction_event_unknown_source_fails_at_model_construction():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    with pytest.raises(ValueError, match="unknown source species"):
        Model(
            grid,
            {"focal": (LinearSuitability((), "alpha", {}),)},
            (
                InteractionEventCount(
                    "events",
                    source_species="missing",
                    effort=EffortField({grid.keys[0]: 1.0}),
                    detection=KnownDetection(1.0),
                    event_logit_parameter="event_logit",
                    informs=frozenset({"suitability"}),
                    targets=frozenset({"focal"}),
                ),
            ),
        )


def test_interaction_event_requires_source_log_intensity_channel():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))

    class FakeSourceProcess:
        name = "source_state"
        output_channel = "state"
        requires = frozenset()
        latent_species_dependencies = frozenset()
        knockout_semantics = "none"
        def priors(self):
            return {}
        def contribution(self, ctx, theta, covariates, latent_fields=None):
            from esdm.process import ProcessContribution
            return ProcessContribution("state", (0.0, 0.0), ("a", "b"))
        def contribution_array(self, keys, theta, covariates, *, array_module, latent_fields=None):
            from esdm.process import ProcessContribution
            return ProcessContribution(
                "state",
                array_module.zeros((len(keys), 2)),
                ("a", "b"),
            )
        def knockout(self):
            return self

    event = InteractionEventCount(
        "events",
        source_species="source",
        effort=EffortField({grid.keys[0]: 1.0}),
        detection=KnownDetection(1.0),
        event_logit_parameter="event_logit",
        informs=frozenset({"suitability"}),
        targets=frozenset({"focal"}),
    )
    model = Model(
        grid,
        {
            "source": (FakeSourceProcess(),),
            "focal": (LinearSuitability((), "alpha", {}),),
        },
        (event,),
    )
    with pytest.raises(DesignUninformedError, match="source.*log_intensity"):
        model.check_design()
