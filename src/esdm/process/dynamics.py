"""Marginal colonization-extinction occupancy dynamics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
import math

from .base import PriorSpec, ProcessContribution


_KNOCKOUT = "set_marginal_occupancy_probability_to_one"


def _sigmoid(value) -> float:
    numeric = float(value)
    if numeric >= 0.0:
        z = math.exp(-numeric)
        return 1.0 / (1.0 + z)
    z = math.exp(numeric)
    return z / (1.0 + z)


def _clean_covariates(values) -> tuple[str, ...]:
    cleaned = tuple(str(value).strip() for value in values)
    if any(not value for value in cleaned) or len(set(cleaned)) != len(cleaned):
        raise ValueError("dynamic occupancy covariates must be unique non-empty names")
    return cleaned


def _clean_coefficients(covariates, values, *, label: str):
    cleaned = {
        str(key).strip(): str(value).strip()
        for key, value in values.items()
    }
    if set(cleaned) != set(covariates):
        raise ValueError(f"{label} coefficient_parameters must match covariates exactly")
    if any(not key or not value for key, value in cleaned.items()):
        raise ValueError(f"{label} coefficient parameter names must be non-empty")
    return MappingProxyType(cleaned)


def _clean_parameter(value: str, *, label: str) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    return cleaned


def _trajectory_indices(keys):
    by_space: dict[str, list[int]] = {}
    for index, key in enumerate(keys):
        if not isinstance(key, tuple) or len(key) != 3:
            raise ValueError("dynamic occupancy keys must be (space, doy, hour)")
        space = str(key[0])
        by_space.setdefault(space, []).append(index)
    return tuple(
        tuple(sorted(indices, key=lambda i: (int(keys[i][1]), int(keys[i][2]))))
        for _, indices in sorted(by_space.items())
    )


@dataclass(frozen=True, slots=True)
class NeutralOccupancy:
    """Occupancy knockout corresponding to no occupancy limitation."""

    name: str = "occupancy"
    output_channel: str = "occupancy"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("occupancy process name must be non-empty")
        object.__setattr__(self, "name", name)

    def priors(self) -> dict[str, PriorSpec]:
        return {}

    def occupancy_values(self, keys, theta, covariates):
        return {key: 1.0 for key in keys}

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        return ProcessContribution(self.output_channel, 1.0)

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        return ProcessContribution(
            self.output_channel,
            array_module.ones((len(keys),)),
        )

    def knockout(self) -> "NeutralOccupancy":
        return self


@dataclass(frozen=True, slots=True)
class ColonizationExtinctionOccupancy:
    """Marginal two-state Markov occupancy across ordered sampling contexts.

    For each spatial unit, contexts are ordered chronologically by (doy, hour).
    The first context has occupancy probability psi0. Every later declared
    sampling context applies exactly one transition:

        psi_t = psi_previous * (1 - epsilon_t)
                + (1 - psi_previous) * gamma_t

    Colonization gamma and extinction epsilon are logistic functions of their
    declared destination-context covariates.

    This is a marginal occupancy recursion. It does not represent a realized
    latent occupancy history, movement path, dispersal kernel, or source-sink process.
    """

    initial_logit_parameter: str
    colonization_intercept_parameter: str
    extinction_intercept_parameter: str
    colonization_covariates: tuple[str, ...] = ()
    colonization_coefficient_parameters: Mapping[str, str] = MappingProxyType({})
    extinction_covariates: tuple[str, ...] = ()
    extinction_coefficient_parameters: Mapping[str, str] = MappingProxyType({})
    name: str = "occupancy"
    output_channel: str = "occupancy"
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        initial = _clean_parameter(
            self.initial_logit_parameter, label="initial_logit_parameter"
        )
        colonization = _clean_parameter(
            self.colonization_intercept_parameter,
            label="colonization_intercept_parameter",
        )
        extinction = _clean_parameter(
            self.extinction_intercept_parameter,
            label="extinction_intercept_parameter",
        )
        col_covariates = _clean_covariates(self.colonization_covariates)
        ext_covariates = _clean_covariates(self.extinction_covariates)
        col_coefficients = _clean_coefficients(
            col_covariates,
            self.colonization_coefficient_parameters,
            label="colonization",
        )
        ext_coefficients = _clean_coefficients(
            ext_covariates,
            self.extinction_coefficient_parameters,
            label="extinction",
        )
        parameter_names = (
            initial,
            colonization,
            extinction,
            *col_coefficients.values(),
            *ext_coefficients.values(),
        )
        if len(set(parameter_names)) != len(parameter_names):
            raise ValueError("dynamic occupancy parameter names must be unique")
        name = str(self.name).strip()
        if not name:
            raise ValueError("occupancy process name must be non-empty")

        object.__setattr__(self, "initial_logit_parameter", initial)
        object.__setattr__(
            self, "colonization_intercept_parameter", colonization
        )
        object.__setattr__(self, "extinction_intercept_parameter", extinction)
        object.__setattr__(self, "colonization_covariates", col_covariates)
        object.__setattr__(
            self,
            "colonization_coefficient_parameters",
            col_coefficients,
        )
        object.__setattr__(self, "extinction_covariates", ext_covariates)
        object.__setattr__(
            self,
            "extinction_coefficient_parameters",
            ext_coefficients,
        )
        object.__setattr__(self, "name", name)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(
            set(self.colonization_covariates) | set(self.extinction_covariates)
        )

    def priors(self) -> dict[str, PriorSpec]:
        priors = {
            self.initial_logit_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 2.0}
            ),
            self.colonization_intercept_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 2.0}
            ),
            self.extinction_intercept_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 2.0}
            ),
        }
        for parameter in self.colonization_coefficient_parameters.values():
            priors[parameter] = PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        for parameter in self.extinction_coefficient_parameters.values():
            priors[parameter] = PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        return priors

    def _scalar_linear_predictor(
        self,
        key,
        theta,
        covariates,
        *,
        intercept_parameter,
        declared_covariates,
        coefficient_parameters,
    ):
        value = theta[intercept_parameter]
        if key not in covariates:
            raise KeyError(f"missing dynamic occupancy covariates for {key!r}")
        for covariate in declared_covariates:
            if covariate not in covariates[key]:
                raise KeyError(
                    f"missing dynamic occupancy covariate {covariate!r} for {key!r}"
                )
            value = (
                value
                + theta[coefficient_parameters[covariate]]
                * covariates[key][covariate]
            )
        return value

    def occupancy_values(self, keys, theta, covariates):
        keys = tuple(keys)
        required = self.requires
        for key in keys:
            if key not in covariates:
                raise KeyError(f"missing dynamic occupancy covariates for {key!r}")
            missing = required - set(covariates[key])
            if missing:
                raise KeyError(
                    f"missing dynamic occupancy covariate {sorted(missing)[0]!r} "
                    f"for {key!r}"
                )

        values: dict[tuple[str, int, int], float] = {}
        for indices in _trajectory_indices(keys):
            psi = _sigmoid(theta[self.initial_logit_parameter])
            first = indices[0]
            values[keys[first]] = psi
            for index in indices[1:]:
                key = keys[index]
                gamma = _sigmoid(
                    self._scalar_linear_predictor(
                        key,
                        theta,
                        covariates,
                        intercept_parameter=self.colonization_intercept_parameter,
                        declared_covariates=self.colonization_covariates,
                        coefficient_parameters=self.colonization_coefficient_parameters,
                    )
                )
                epsilon = _sigmoid(
                    self._scalar_linear_predictor(
                        key,
                        theta,
                        covariates,
                        intercept_parameter=self.extinction_intercept_parameter,
                        declared_covariates=self.extinction_covariates,
                        coefficient_parameters=self.extinction_coefficient_parameters,
                    )
                )
                psi = psi * (1.0 - epsilon) + (1.0 - psi) * gamma
                values[key] = psi
        return {key: values[key] for key in keys}

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        raise TypeError(
            "ColonizationExtinctionOccupancy requires an ordered context sequence; "
            "evaluate it through Model.latent_fields(...)"
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
        keys = tuple(keys)
        missing = self.requires - set(covariates)
        if missing:
            raise KeyError(
                f"missing dynamic occupancy covariate array {sorted(missing)[0]!r}"
            )

        def logistic(value):
            return array_module.exp(
                -array_module.logaddexp(array_module.asarray(0.0), -value)
            )

        result = [None] * len(keys)
        for indices in _trajectory_indices(keys):
            psi = logistic(theta[self.initial_logit_parameter])
            result[indices[0]] = psi
            for index in indices[1:]:
                gamma_eta = theta[self.colonization_intercept_parameter]
                for covariate in self.colonization_covariates:
                    gamma_eta = (
                        gamma_eta
                        + theta[self.colonization_coefficient_parameters[covariate]]
                        * covariates[covariate][index]
                    )
                epsilon_eta = theta[self.extinction_intercept_parameter]
                for covariate in self.extinction_covariates:
                    epsilon_eta = (
                        epsilon_eta
                        + theta[self.extinction_coefficient_parameters[covariate]]
                        * covariates[covariate][index]
                    )
                gamma = logistic(gamma_eta)
                epsilon = logistic(epsilon_eta)
                psi = psi * (1.0 - epsilon) + (1.0 - psi) * gamma
                result[index] = psi

        return ProcessContribution(
            self.output_channel,
            array_module.stack(tuple(result)),
        )

    def knockout(self) -> NeutralOccupancy:
        return NeutralOccupancy(name=self.name)
