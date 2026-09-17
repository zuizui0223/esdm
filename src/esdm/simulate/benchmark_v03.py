"""Matched v0.3 benchmark worlds for promotion-gate validation.

In-model worlds are generated through the exact production Model/process/stream graph.
Misspecified worlds keep the same generated records but deliberately alter the model
available to fitting, or generate from a richer graph than the fitted graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability
from esdm.simulate.in_model import simulate_presence_only


Key = tuple[str, int, int]


@dataclass(frozen=True, slots=True)
class V03BenchmarkWorld:
    name: str
    kind: str
    truth_process_present: bool
    counts: Mapping[str, Mapping[str, Mapping[Key, int]]]
    truth_log_intensity: tuple[float, ...]
    true_effort: tuple[float, ...]
    fit_effort: tuple[float, ...]
    fit_covariates: Mapping[str, tuple[float, ...]]
    hidden_log_contribution: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in {"in_model", "misspecified"}:
            raise ValueError("kind must be 'in_model' or 'misspecified'")
        object.__setattr__(self, "counts", MappingProxyType(dict(self.counts)))
        object.__setattr__(self, "fit_covariates", MappingProxyType(dict(self.fit_covariates)))


def _geometry():
    spaces = tuple(f"s{i}" for i in range(8))
    grid = Grid(space=spaces, doy=(1,), hour=(0,))
    keys = tuple(grid.keys)
    observed = (-1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75)
    effort = (0.5, 1.0, 2.0, 4.0, 4.0, 2.0, 1.0, 0.5)
    return grid, keys, observed, effort


def _effort_field(keys, values):
    return EffortField({key: value for key, value in zip(keys, values)})


def _suitability(covariates: tuple[str, ...]):
    return LinearSuitability(
        covariates=covariates,
        intercept_parameter="alpha",
        coefficient_parameters={name: f"beta_{name}" for name in covariates},
    )


def _model(grid, effort_values, covariates):
    keys = tuple(grid.keys)
    process = _suitability(tuple(covariates))
    stream = PresenceOnly(
        "records",
        effort=_effort_field(keys, effort_values),
        informs=frozenset({"suitability"}),
    )
    return Model(domain=grid, species={"species": (process,)}, streams=(stream,))


def _covariate_map(keys, **columns):
    return {
        key: {name: values[i] for name, values in columns.items()}
        for i, key in enumerate(keys)
    }


def _world_from_model(*, name, kind, model, theta, covariates, seed, fit_effort, fit_covariates, truth_process_present, hidden=()):
    generated = simulate_presence_only(model, theta, covariates, seed=seed)
    fields = model.latent_fields(theta, covariates)
    keys = tuple(model.domain.keys)
    stream = model.streams[0]
    true_effort = tuple(stream.effort.at(key) for key in keys)
    return V03BenchmarkWorld(
        name=name,
        kind=kind,
        truth_process_present=truth_process_present,
        counts=generated.counts,
        truth_log_intensity=tuple(float(fields.log_intensity["species"][key]) for key in keys),
        true_effort=true_effort,
        fit_effort=tuple(float(x) for x in fit_effort),
        fit_covariates={name: tuple(float(x) for x in values) for name, values in fit_covariates.items()},
        hidden_log_contribution=tuple(float(x) for x in hidden),
    )


def make_correct_effort_world(*, seed: int = 0) -> V03BenchmarkWorld:
    grid, keys, observed, effort = _geometry()
    model = _model(grid, effort, ("observed_env",))
    covariates = _covariate_map(keys, observed_env=observed)
    theta = {"species": {"alpha": -0.1, "beta_observed_env": 0.8}}
    return _world_from_model(
        name="correct_effort",
        kind="in_model",
        model=model,
        theta=theta,
        covariates=covariates,
        seed=seed,
        fit_effort=effort,
        fit_covariates={"observed_env": observed},
        truth_process_present=True,
    )


def make_wrong_effort_world(*, seed: int = 0) -> V03BenchmarkWorld:
    grid, keys, observed, effort = _geometry()
    model = _model(grid, effort, ("observed_env",))
    covariates = _covariate_map(keys, observed_env=observed)
    theta = {"species": {"alpha": -0.1, "beta_observed_env": 0.8}}
    assumed = (1.0,) * len(effort)
    return _world_from_model(
        name="wrong_effort_geometry",
        kind="misspecified",
        model=model,
        theta=theta,
        covariates=covariates,
        seed=seed,
        fit_effort=assumed,
        fit_covariates={"observed_env": observed},
        truth_process_present=True,
    )


def make_hidden_driver_world(*, seed: int = 0) -> V03BenchmarkWorld:
    grid, keys, observed, effort = _geometry()
    hidden = (-1.2, -0.8, -0.4, 0.2, 0.6, 1.0, 0.8, 0.3)
    beta_hidden = 0.9
    model = _model(grid, effort, ("observed_env", "hidden_env"))
    covariates = _covariate_map(keys, observed_env=observed, hidden_env=hidden)
    theta = {
        "species": {
            "alpha": -0.1,
            "beta_observed_env": 0.5,
            "beta_hidden_env": beta_hidden,
        }
    }
    return _world_from_model(
        name="hidden_environmental_driver",
        kind="misspecified",
        model=model,
        theta=theta,
        covariates=covariates,
        seed=seed,
        fit_effort=effort,
        fit_covariates={"observed_env": observed},
        truth_process_present=True,
        hidden=tuple(beta_hidden * value for value in hidden),
    )


def make_knockout_world(*, seed: int = 0) -> V03BenchmarkWorld:
    grid, keys, observed, effort = _geometry()
    full = _model(grid, effort, ("observed_env",))
    model = full.knockout("species", "suitability")
    covariates = _covariate_map(keys, observed_env=observed)
    theta = {"species": {}}
    return _world_from_model(
        name="suitability_knockout",
        kind="in_model",
        model=model,
        theta=theta,
        covariates=covariates,
        seed=seed,
        fit_effort=effort,
        fit_covariates={"observed_env": observed},
        truth_process_present=False,
    )
