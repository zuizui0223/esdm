"""Memoryless static occupancy process for matched dynamic benchmarks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
import math

from .base import PriorSpec, ProcessContribution
from .dynamics import NeutralOccupancy


def _sigmoid(value) -> float:
    numeric = float(value)
    if numeric >= 0.0:
        z = math.exp(-numeric)
        return 1.0 / (1.0 + z)
    z = math.exp(numeric)
    return z / (1.0 + z)


@dataclass(frozen=True, slots=True)
class StaticLinearOccupancy:
    """Memoryless logistic occupancy over declared context covariates.

    Each context is evaluated independently as a logistic function of the
    declared covariates. There is no dependence on previous occupancy. This
    makes the process a lower-resolution static comparator for the recursive
    colonization/extinction occupancy model while retaining the same semantic
    occupancy channel.
    """

    covariates: tuple[str, ...]
    intercept_parameter: str
    coefficient_parameters: Mapping[str, str]
    name: str = "occupancy"
    output_channel: str = "occupancy"
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "set_marginal_occupancy_probability_to_one"

    def __post_init__(self) -> None:
        covariates = tuple(str(value).strip() for value in self.covariates)
        if (
            len(set(covariates)) != len(covariates)
            or any(not value for value in covariates)
        ):
            raise ValueError(
                "static occupancy covariates must be unique non-empty names"
            )
        intercept = str(self.intercept_parameter).strip()
        if not intercept:
            raise ValueError("intercept_parameter must be non-empty")
        coefficients = {
            str(key).strip(): str(value).strip()
            for key, value in self.coefficient_parameters.items()
        }
        if set(coefficients) != set(covariates):
            raise ValueError(
                "coefficient_parameters must match covariates exactly"
            )
        if any(not key or not value for key, value in coefficients.items()):
            raise ValueError(
                "static occupancy coefficient parameter names must be non-empty"
            )
        if len(set(coefficients.values())) != len(coefficients):
            raise ValueError(
                "static occupancy coefficient parameter names must be unique"
            )
        if intercept in set(coefficients.values()):
            raise ValueError(
                "static occupancy intercept and coefficient names must be unique"
            )
        name = str(self.name).strip()
        if not name:
            raise ValueError("occupancy process name must be non-empty")

        object.__setattr__(self, "covariates", covariates)
        object.__setattr__(self, "intercept_parameter", intercept)
        object.__setattr__(
            self,
            "coefficient_parameters",
            MappingProxyType(coefficients),
        )
        object.__setattr__(self, "name", name)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(self.covariates)

    def priors(self) -> dict[str, PriorSpec]:
        priors = {
            self.intercept_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 2.0}
            )
        }
        for parameter in self.coefficient_parameters.values():
            priors[parameter] = PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        return priors

    def _linear_predictor(self, theta, covariates):
        value = theta[self.intercept_parameter]
        for covariate in self.covariates:
            if covariate not in covariates:
                raise KeyError(
                    f"missing static occupancy covariate {covariate!r}"
                )
            value = (
                value
                + theta[self.coefficient_parameters[covariate]]
                * covariates[covariate]
            )
        return value

    def occupancy_values(self, keys, theta, covariates):
        values = {}
        for key in keys:
            if key not in covariates:
                raise KeyError(
                    f"missing static occupancy covariates for {key!r}"
                )
            values[key] = _sigmoid(
                self._linear_predictor(theta, covariates[key])
            )
        return values

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        return ProcessContribution(
            self.output_channel,
            _sigmoid(self._linear_predictor(theta, covariates)),
        )

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        eta = array_module.broadcast_to(
            array_module.asarray(theta[self.intercept_parameter]),
            (len(keys),),
        )
        for covariate in self.covariates:
            if covariate not in covariates:
                raise KeyError(
                    f"missing static occupancy covariate array {covariate!r}"
                )
            eta = (
                eta
                + theta[self.coefficient_parameters[covariate]]
                * covariates[covariate]
            )
        values = array_module.exp(
            -array_module.logaddexp(
                array_module.asarray(0.0),
                -eta,
            )
        )
        return ProcessContribution(self.output_channel, values)

    def knockout(self) -> NeutralOccupancy:
        return NeutralOccupancy(name=self.name)
