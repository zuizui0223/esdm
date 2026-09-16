"""Identifiable two-stream fixture for the frozen v0.3.1 SBC gate."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, LogLinearEffort, PresenceOnly
from esdm.process import LinearSuitability


@dataclass(frozen=True, slots=True)
class V031SBCFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    reference_theta: Mapping[str, Mapping[str, float]]
    reference_theta_obs: Mapping[str, Mapping[str, float]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType(
                {key: MappingProxyType(dict(values)) for key, values in self.covariates.items()}
            ),
        )
        object.__setattr__(
            self,
            "reference_theta",
            MappingProxyType(
                {name: MappingProxyType(dict(values)) for name, values in self.reference_theta.items()}
            ),
        )
        object.__setattr__(
            self,
            "reference_theta_obs",
            MappingProxyType(
                {name: MappingProxyType(dict(values)) for name, values in self.reference_theta_obs.items()}
            ),
        )


def make_v031_sbc_fixture() -> V031SBCFixture:
    """Return a structurally identifiable ecological/observation-process fixture.

    The opportunistic stream has an unknown effort slope ``gamma_x``. A second stream
    has known non-constant effort and observes the same ecological field, breaking the
    otherwise exact ``beta_x + gamma_x`` confounding. This fixture is intentionally
    domain-neutral: it represents no particular taxon or interaction family.
    """

    x = (-1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75)
    grid = Grid(space=tuple(f"s{i}" for i in range(len(x))), doy=(1,), hour=(0,))
    covariates = {
        key: {"x": float(x[index])}
        for index, key in enumerate(grid.keys)
    }
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    opportunistic = PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(
            baseline=5.0,
            covariate="x",
            coefficient_parameter="gamma_x",
        ),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    calibrated_effort_values = (2.0, 5.0, 3.0, 7.0, 4.0, 6.0, 2.5, 5.5)
    calibrated = PresenceOnly(
        name="calibrated",
        effort=EffortField(
            {
                key: calibrated_effort_values[index]
                for index, key in enumerate(grid.keys)
            }
        ),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=grid,
        species={"sp": (process,)},
        streams=(opportunistic, calibrated),
    )
    model.check_design()
    return V031SBCFixture(
        model=model,
        covariates=covariates,
        reference_theta={"sp": {"intercept": 1.5, "beta_x": 0.6}},
        reference_theta_obs={
            "opportunistic": {"gamma_x": 0.7},
            "calibrated": {},
        },
    )
