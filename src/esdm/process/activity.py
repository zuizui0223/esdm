"""Environmental contribution to conditional ecological activity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .base import PriorSpec, ProcessContribution


_KNOCKOUT = "preserve_baseline_neutralize_environmental_slopes"


@dataclass(frozen=True, slots=True)
class NeutralActivity:
    """Activity knockout preserving baseline logit while removing gradients."""

    intercept_parameter: str
    name: str = "activity"
    output_channel: str = "activity"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        intercept = str(self.intercept_parameter).strip()
        name = str(self.name).strip()
        if not intercept:
            raise ValueError("intercept_parameter must be non-empty")
        if not name:
            raise ValueError("activity process name must be non-empty")
        object.__setattr__(self, "intercept_parameter", intercept)
        object.__setattr__(self, "name", name)

    def priors(self) -> dict[str, PriorSpec]:
        return {
            self.intercept_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 2.0}
            )
        }

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        return ProcessContribution(
            self.output_channel,
            theta[self.intercept_parameter],
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
        baseline = array_module.asarray(theta[self.intercept_parameter])
        return ProcessContribution(
            self.output_channel,
            array_module.broadcast_to(baseline, (len(keys),)),
        )

    def knockout(self) -> "NeutralActivity":
        return self


@dataclass(frozen=True, slots=True)
class LinearActivity:
    """Environmental model for the activity logit conditional on availability."""

    covariates: tuple[str, ...]
    intercept_parameter: str
    coefficient_parameters: Mapping[str, str]
    name: str = "activity"
    output_channel: str = "activity"
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        covariates = tuple(str(value).strip() for value in self.covariates)
        if (
            len(set(covariates)) != len(covariates)
            or any(not value for value in covariates)
        ):
            raise ValueError("covariates must be unique non-empty names")
        intercept = str(self.intercept_parameter).strip()
        if not intercept:
            raise ValueError("intercept_parameter must be non-empty")
        coefficients = {
            str(key).strip(): str(value).strip()
            for key, value in self.coefficient_parameters.items()
        }
        if set(coefficients) != set(covariates):
            raise ValueError("coefficient_parameters must match covariates exactly")
        if any(not key or not value for key, value in coefficients.items()):
            raise ValueError("coefficient parameter names must be non-empty")
        name = str(self.name).strip()
        if not name:
            raise ValueError("activity process name must be non-empty")
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

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        value = theta[self.intercept_parameter]
        for covariate in self.covariates:
            value = (
                value
                + theta[self.coefficient_parameters[covariate]]
                * covariates[covariate]
            )
        return ProcessContribution(self.output_channel, value)

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        value = array_module.broadcast_to(
            array_module.asarray(theta[self.intercept_parameter]),
            (len(keys),),
        )
        for covariate in self.covariates:
            if covariate not in covariates:
                raise KeyError(
                    f"missing activity covariate array {covariate!r}"
                )
            value = (
                value
                + theta[self.coefficient_parameters[covariate]]
                * covariates[covariate]
            )
        return ProcessContribution(self.output_channel, value)

    def knockout(self) -> NeutralActivity:
        return NeutralActivity(
            intercept_parameter=self.intercept_parameter,
            name=self.name,
        )
