"""Environmental contribution to latent accessibility probability."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
import math

from .base import PriorSpec, ProcessContribution


_KNOCKOUT = "set_accessibility_probability_to_one"


def _log_sigmoid(value) -> float:
    numeric = float(value)
    if numeric >= 0.0:
        return -math.log1p(math.exp(-numeric))
    return numeric - math.log1p(math.exp(numeric))


@dataclass(frozen=True, slots=True)
class NeutralAccessibility:
    """Accessibility knockout corresponding to no accessibility limitation."""

    name: str = "accessibility"
    output_channel: str = "log_accessibility"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("accessibility process name must be non-empty")
        object.__setattr__(self, "name", name)

    def priors(self) -> dict[str, PriorSpec]:
        return {}

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        return ProcessContribution(self.output_channel, 0.0)

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
            array_module.zeros((len(keys),)),
        )

    def knockout(self) -> "NeutralAccessibility":
        return self


@dataclass(frozen=True, slots=True)
class LinearAccessibility:
    """Logistic accessibility probability over declared environmental covariates.

    The process contributes log(accessibility), so multiple accessibility processes
    combine multiplicatively and the explicit neutral element is log(1)=0.
    """

    covariates: tuple[str, ...]
    intercept_parameter: str
    coefficient_parameters: Mapping[str, str]
    name: str = "accessibility"
    output_channel: str = "log_accessibility"
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
            raise ValueError("accessibility process name must be non-empty")
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
            value = (
                value
                + theta[self.coefficient_parameters[covariate]]
                * covariates[covariate]
            )
        return value

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        return ProcessContribution(
            self.output_channel,
            _log_sigmoid(self._linear_predictor(theta, covariates)),
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
                    f"missing accessibility covariate array {covariate!r}"
                )
            eta = (
                eta
                + theta[self.coefficient_parameters[covariate]]
                * covariates[covariate]
            )
        log_accessibility = -array_module.logaddexp(
            array_module.asarray(0.0),
            -eta,
        )
        return ProcessContribution(
            self.output_channel,
            log_accessibility,
        )

    def knockout(self) -> NeutralAccessibility:
        return NeutralAccessibility(name=self.name)
