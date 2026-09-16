"""Environmental suitability contribution to ecological log intensity."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from esdm.domain import Context
from .base import NoEffectProcess, PriorSpec


@dataclass(frozen=True, slots=True)
class LinearSuitability:
    covariates: tuple[str, ...]
    intercept_parameter: str
    coefficient_parameters: Mapping[str, str]
    name: str = "suitability"
    output_channel: str = "log_intensity"
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "no_effect_log_contribution_zero"

    def __post_init__(self) -> None:
        covariates = tuple(str(value).strip() for value in self.covariates)
        if len(set(covariates)) != len(covariates) or any(not value for value in covariates):
            raise ValueError("covariates must be unique non-empty names")
        intercept = str(self.intercept_parameter).strip()
        if not intercept:
            raise ValueError("intercept_parameter must be non-empty")
        coefficients = {str(k).strip(): str(v).strip() for k, v in self.coefficient_parameters.items()}
        if set(coefficients) != set(covariates):
            raise ValueError("coefficient_parameters must match covariates exactly")
        if any(not key or not value for key, value in coefficients.items()):
            raise ValueError("coefficient parameter names must be non-empty")
        object.__setattr__(self, "covariates", covariates)
        object.__setattr__(self, "intercept_parameter", intercept)
        object.__setattr__(self, "coefficient_parameters", MappingProxyType(coefficients))

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(self.covariates)

    def priors(self) -> dict[str, PriorSpec]:
        priors = {self.intercept_parameter: PriorSpec("Normal", {"loc": 0.0, "scale": 2.0})}
        for parameter in self.coefficient_parameters.values():
            priors[parameter] = PriorSpec("Normal", {"loc": 0.0, "scale": 1.0})
        return priors

    def log_intensity(self, ctx: Context, theta, covariates, latent_fields=None):
        """Return this process' additive log-intensity contribution.

        The arithmetic deliberately avoids coercing values to Python ``float`` so the
        exact same process implementation can operate on ordinary scalars and on JAX
        tracer values inside the optional NumPyro backend.
        """

        value = theta[self.intercept_parameter]
        for covariate in self.covariates:
            value = value + theta[self.coefficient_parameters[covariate]] * covariates[covariate]
        return value

    def knockout(self) -> NoEffectProcess:
        return NoEffectProcess(name=self.name)
