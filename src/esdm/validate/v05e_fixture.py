"""Fresh evidence-separation worlds for v0.5e."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from esdm.model import Model
from esdm.observe import EffortField, PairEventCount
from .v05a_directed import build_v05a_fixture, v05a_theta
from .v05b_hidden_driver import build_v05b_fixture


V05E_WORLDS = (
    "hidden_event_silent",
    "realized_only",
    "directed_realized",
)

V05E_BETA_SITE = "focal.partner_effect.beta_partner"
V05E_EVENT_SITE = "stream.events.event_intercept"


@dataclass(frozen=True, slots=True)
class V05EFixture:
    fitting_model: Model
    generating_model: Model
    fitting_covariates: dict
    generating_covariates: dict
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: dict
    generating_theta_obs: dict
    world: str

    def __post_init__(self) -> None:
        if self.world not in V05E_WORLDS:
            raise ValueError("unknown v0.5e world")
        for name in ("fitting_covariates", "generating_covariates"):
            object.__setattr__(
                self,
                name,
                MappingProxyType({
                    key: MappingProxyType(dict(values))
                    for key, values in getattr(self, name).items()
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
    return PairEventCount(
        name="events",
        source_species="source",
        target_species="focal",
        effort=EffortField({
            key: 2.0
            for key in domain.keys
            if key[0] in train
        }),
        event_intercept_parameter="event_intercept",
        informs=frozenset({"partner_effect"}),
    )


def _with_event_stream(model, train_spaces):
    events = _event_stream(model.domain, train_spaces)
    combined = Model(
        domain=model.domain,
        species=model.species,
        streams=(*model.streams, events),
    )
    combined.check_design()
    return combined


def build_v05e_fixture(world: str) -> V05EFixture:
    name = str(world)
    if name not in V05E_WORLDS:
        raise ValueError("unknown v0.5e world")

    if name == "hidden_event_silent":
        hidden = build_v05b_fixture()
        fitting_model = _with_event_stream(
            hidden.fitting_model,
            hidden.train_spaces,
        )
        generating_model = _with_event_stream(
            hidden.generating_model,
            hidden.train_spaces,
        )
        theta = {
            species: dict(values)
            for species, values in hidden.generating_theta.items()
        }
        theta_obs = {
            stream: dict(values)
            for stream, values in hidden.theta_obs.items()
        }
        theta_obs["events"] = {"event_intercept": -8.0}
        return V05EFixture(
            fitting_model=fitting_model,
            generating_model=generating_model,
            fitting_covariates={
                key: dict(values)
                for key, values in hidden.fitting_covariates.items()
            },
            generating_covariates={
                key: dict(values)
                for key, values in hidden.generating_covariates.items()
            },
            train_spaces=hidden.train_spaces,
            heldout_spaces=hidden.heldout_spaces,
            generating_theta=theta,
            generating_theta_obs=theta_obs,
            world=name,
        )

    base = build_v05a_fixture()
    model = _with_event_stream(base.model, base.train_spaces)
    truth_world = (
        "measured_shared_null"
        if name == "realized_only"
        else "interaction"
    )
    theta = v05a_theta(base, truth_world)
    theta_obs = {
        stream: dict(values)
        for stream, values in base.theta_obs.items()
    }
    theta_obs["events"] = {"event_intercept": -1.0}
    return V05EFixture(
        fitting_model=model,
        generating_model=model,
        fitting_covariates={
            key: dict(values)
            for key, values in base.covariates.items()
        },
        generating_covariates={
            key: dict(values)
            for key, values in base.covariates.items()
        },
        train_spaces=base.train_spaces,
        heldout_spaces=base.heldout_spaces,
        generating_theta=theta,
        generating_theta_obs=theta_obs,
        world=name,
    )
