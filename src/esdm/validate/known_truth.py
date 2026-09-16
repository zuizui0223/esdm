"""Generic v0.3 known-truth benchmark worlds.

The worlds are deliberately ecological-domain neutral.  They exercise the generative
contracts around suitability, observation effort, omitted environmental structure, and
process knockout before any interaction family is added.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability
from esdm.simulate.misspecified import (
    effort_gradient_apparent_slope,
    omitted_driver_apparent_slope,
)


@dataclass(frozen=True, slots=True)
class KnownTruthWorld:
    name: str
    generating_model: Model
    fitting_model: Model
    generating_covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    fitting_covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    generating_theta: Mapping[str, Mapping[str, float]]
    truth: Mapping[str, float]
    target_parameter: str
    expected_apparent_value: float
    world_class: str

    def __post_init__(self) -> None:
        if self.world_class not in {"in_model", "misspecified", "knockout"}:
            raise ValueError("unknown known-truth world_class")
        if self.target_parameter not in self.truth:
            raise ValueError("truth must contain target_parameter")
        object.__setattr__(
            self,
            "generating_covariates",
            MappingProxyType({key: MappingProxyType(dict(values)) for key, values in self.generating_covariates.items()}),
        )
        object.__setattr__(
            self,
            "fitting_covariates",
            MappingProxyType({key: MappingProxyType(dict(values)) for key, values in self.fitting_covariates.items()}),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType({species: MappingProxyType(dict(values)) for species, values in self.generating_theta.items()}),
        )
        object.__setattr__(self, "truth", MappingProxyType(dict(self.truth)))


def _grid_and_x() -> tuple[Grid, tuple[float, ...]]:
    x = (-1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75)
    grid = Grid(space=tuple(f"s{i}" for i in range(len(x))), doy=(1,), hour=(0,))
    return grid, x


def _covariates(grid: Grid, **columns: tuple[float, ...]):
    for name, values in columns.items():
        if len(values) != len(grid.keys):
            raise ValueError(f"covariate {name!r} length does not match domain")
    return {
        key: {name: float(values[index]) for name, values in columns.items()}
        for index, key in enumerate(grid.keys)
    }


def _suitability(*covariates: str) -> LinearSuitability:
    coefficient_parameters = {
        covariate: ("beta_x" if covariate == "x" else f"beta_{covariate}")
        for covariate in covariates
    }
    return LinearSuitability(
        covariates=tuple(covariates),
        intercept_parameter="intercept",
        coefficient_parameters=coefficient_parameters,
    )


def _model(grid: Grid, process, effort_values) -> Model:
    effort = EffortField({
        key: float(value)
        for key, value in zip(grid.keys, effort_values, strict=True)
    })
    stream = PresenceOnly(
        name="records",
        effort=effort,
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
    )
    return Model(domain=grid, species={"sp": (process,)}, streams=(stream,))


def make_v03_known_truth_worlds() -> tuple[KnownTruthWorld, ...]:
    """Return the frozen generic v0.3 benchmark universe.

    The first and fourth worlds are in-model/knockout controls.  The middle two are
    deliberate misspecifications and therefore are not SBC worlds.
    """

    grid, x = _grid_and_x()
    target = "sp.suitability.beta_x"

    # 1) Correct observation geometry: heterogeneous effort is modelled as generated.
    correct_effort = (5.0, 8.0, 5.0, 8.0, 8.0, 5.0, 8.0, 5.0)
    correct_process = _suitability("x")
    correct_model = _model(grid, correct_process, correct_effort)
    correct_covariates = _covariates(grid, x=x)
    correct_truth = 0.6
    correct = KnownTruthWorld(
        name="correct_effort",
        generating_model=correct_model,
        fitting_model=correct_model,
        generating_covariates=correct_covariates,
        fitting_covariates=correct_covariates,
        generating_theta={"sp": {"intercept": 2.0, "beta_x": correct_truth}},
        truth={target: correct_truth},
        target_parameter=target,
        expected_apparent_value=correct_truth,
        world_class="in_model",
    )

    # 2) Observation-process misspecification: effort is correlated with x but fit as flat.
    gamma_effort = 0.7
    effort_scale = 5.0
    true_effort = tuple(effort_scale * math.exp(gamma_effort * value) for value in x)
    wrong_fit_effort = tuple(effort_scale for _ in x)
    wrong_generating_model = _model(grid, _suitability("x"), true_effort)
    wrong_fitting_model = _model(grid, _suitability("x"), wrong_fit_effort)
    wrong_truth = 0.6
    wrong_expected = effort_gradient_apparent_slope(
        true_beta=wrong_truth,
        covariate=x,
        true_effort=true_effort,
        assumed_effort=effort_scale,
    )
    wrong = KnownTruthWorld(
        name="wrong_effort_geometry",
        generating_model=wrong_generating_model,
        fitting_model=wrong_fitting_model,
        generating_covariates=correct_covariates,
        fitting_covariates=correct_covariates,
        generating_theta={"sp": {"intercept": 2.0, "beta_x": wrong_truth}},
        truth={target: wrong_truth},
        target_parameter=target,
        expected_apparent_value=wrong_expected,
        world_class="misspecified",
    )

    # 3) Ecological misspecification: a correlated environmental driver is omitted at fit.
    hidden = tuple(0.8 * value for value in x)
    hidden_generating_model = _model(grid, _suitability("x", "hidden"), correct_effort)
    hidden_fitting_model = _model(grid, _suitability("x"), correct_effort)
    beta_x = 0.4
    beta_hidden = 0.75
    hidden_expected = omitted_driver_apparent_slope(
        true_beta=beta_x,
        omitted_beta=beta_hidden,
        covariate=x,
        hidden_driver=hidden,
    )
    hidden_world = KnownTruthWorld(
        name="hidden_driver",
        generating_model=hidden_generating_model,
        fitting_model=hidden_fitting_model,
        generating_covariates=_covariates(grid, x=x, hidden=hidden),
        fitting_covariates=correct_covariates,
        generating_theta={
            "sp": {
                "intercept": 2.0,
                "beta_x": beta_x,
                "beta_hidden": beta_hidden,
            }
        },
        truth={target: beta_x},
        target_parameter=target,
        expected_apparent_value=hidden_expected,
        world_class="misspecified",
    )

    # 4) Structural negative control: suitability is removed from the generating graph.
    full_knockout_fit = _model(grid, _suitability("x"), correct_effort)
    knockout_generating = full_knockout_fit.knockout("sp", "suitability")
    knockout = KnownTruthWorld(
        name="suitability_knockout",
        generating_model=knockout_generating,
        fitting_model=full_knockout_fit,
        generating_covariates=correct_covariates,
        fitting_covariates=correct_covariates,
        generating_theta={"sp": {}},
        truth={target: 0.0},
        target_parameter=target,
        expected_apparent_value=0.0,
        world_class="knockout",
    )

    return (correct, wrong, hidden_world, knockout)
