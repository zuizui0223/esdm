"""Fresh event-gated validation worlds for v0.5c."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.model import Model
from esdm.observe import EffortField, InteractionEventCount, KnownDetection
from .v05a_directed import build_v05a_fixture, v05a_theta
from .v05b_hidden import build_v05b_fixture


V05C_WORLDS = ("interaction_event", "hidden_driver_null")
V05C_BETA_TARGET = "focal.partner_effect.beta_partner"
V05C_EVENT_SITE = "stream.interaction_events.event_logit"
V05C_EVENT_SUPPORT_THRESHOLD = 0.05


def _logit(probability: float) -> float:
    p = float(probability)
    if not 0.0 < p < 1.0:
        raise ValueError("probability must be in (0, 1)")
    return math.log(p / (1.0 - p))


@dataclass(frozen=True, slots=True)
class V05CWorldFixture:
    world: str
    generating_model: Model
    fitting_model: Model
    generating_covariates: dict
    fitting_covariates: dict
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: dict
    generating_theta_obs: dict
    true_event_probability: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generating_covariates",
            MappingProxyType({
                key: MappingProxyType(dict(values))
                for key, values in self.generating_covariates.items()
            }),
        )
        object.__setattr__(
            self,
            "fitting_covariates",
            MappingProxyType({
                key: MappingProxyType(dict(values))
                for key, values in self.fitting_covariates.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType({
                species: MappingProxyType(dict(values))
                for species, values in self.generating_theta.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta_obs",
            MappingProxyType({
                name: MappingProxyType(dict(values))
                for name, values in self.generating_theta_obs.items()
            }),
        )


def _event_stream(domain, train_spaces):
    train = set(train_spaces)
    return InteractionEventCount(
        "interaction_events",
        source_species="source",
        effort=EffortField({
            key: 0.5
            for key in domain.keys
            if key[0] in train
        }),
        detection=KnownDetection(0.9),
        event_logit_parameter="event_logit",
        informs=frozenset({"partner_effect"}),
        targets=frozenset({"focal"}),
    )


def _append_event_stream(model: Model, train_spaces) -> Model:
    event = _event_stream(model.domain, train_spaces)
    output = Model(
        domain=model.domain,
        species=model.species,
        streams=(*model.streams, event),
    )
    output.check_design()
    return output


def build_v05c_world(world: str) -> V05CWorldFixture:
    name = str(world)
    if name not in V05C_WORLDS:
        raise ValueError("unknown v0.5c world")

    if name == "interaction_event":
        base = build_v05a_fixture()
        generating_model = _append_event_stream(
            base.model, base.train_spaces
        )
        fitting_model = generating_model
        theta = v05a_theta(base, "interaction")
        event_probability = 0.25
        theta_obs = {
            stream: dict(values)
            for stream, values in base.theta_obs.items()
        }
        theta_obs["interaction_events"] = {
            "event_logit": _logit(event_probability)
        }
        return V05CWorldFixture(
            world=name,
            generating_model=generating_model,
            fitting_model=fitting_model,
            generating_covariates={
                key: dict(values) for key, values in base.covariates.items()
            },
            fitting_covariates={
                key: dict(values) for key, values in base.covariates.items()
            },
            train_spaces=base.train_spaces,
            heldout_spaces=base.heldout_spaces,
            generating_theta=theta,
            generating_theta_obs=theta_obs,
            true_event_probability=event_probability,
        )

    hidden = build_v05b_fixture()
    generating_model = _append_event_stream(
        hidden.generating_model, hidden.train_spaces
    )
    fitting_model = _append_event_stream(
        hidden.fitting_model, hidden.train_spaces
    )
    event_probability = 0.005
    theta_obs = {
        stream: dict(values)
        for stream, values in hidden.theta_obs.items()
    }
    theta_obs["interaction_events"] = {
        "event_logit": _logit(event_probability)
    }
    return V05CWorldFixture(
        world=name,
        generating_model=generating_model,
        fitting_model=fitting_model,
        generating_covariates={
            key: dict(values)
            for key, values in hidden.generating_covariates.items()
        },
        fitting_covariates={
            key: dict(values)
            for key, values in hidden.fitting_covariates.items()
        },
        train_spaces=hidden.train_spaces,
        heldout_spaces=hidden.heldout_spaces,
        generating_theta={
            species: dict(values)
            for species, values in hidden.generating_theta.items()
        },
        generating_theta_obs=theta_obs,
        true_event_probability=event_probability,
    )


def expected_training_events(fixture: V05CWorldFixture) -> float:
    fields = fixture.generating_model.latent_fields(
        fixture.generating_theta,
        fixture.generating_covariates,
    )
    stream = {
        stream.name: stream
        for stream in fixture.generating_model.streams
    }["interaction_events"]
    block = stream.observation_blocks(
        "focal",
        fields,
        theta_obs=fixture.generating_theta_obs["interaction_events"],
        covariates=fixture.generating_covariates,
    )[0]
    train = set(fixture.train_spaces)
    return math.fsum(
        float(rate)
        for key, rate in zip(block.keys, block.rates, strict=True)
        if key[0] in train
    )
