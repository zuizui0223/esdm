"""Directed biotic effect through a source species latent intensity field."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .base import PriorSpec, ProcessContribution


_KNOCKOUT = "partner_latent_effect_zero"


def _softplus_scalar(value) -> float:
    numeric = float(value)
    if numeric > 0.0:
        return numeric + math.log1p(math.exp(-numeric))
    return math.log1p(math.exp(numeric))


@dataclass(frozen=True, slots=True)
class NeutralPartnerIntensityEffect:
    """No-effect partner process used by explicit process knockout."""

    source_species: str
    name: str
    output_channel: str = "log_intensity"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        source = str(self.source_species).strip()
        name = str(self.name).strip()
        if not source or not name:
            raise ValueError("source_species and name must be non-empty")
        object.__setattr__(self, "source_species", source)
        object.__setattr__(self, "name", name)

    def priors(self):
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

    def knockout(self):
        return self


@dataclass(frozen=True, slots=True)
class PartnerIntensityEffect:
    """Directed focal response to a partner's latent ecological intensity.

    The source latent log-intensity is transformed with softplus so the predictor is a
    positive partner-pressure scale, then multiplied by one signed interaction
    coefficient and added to the focal log-intensity channel.
    """

    source_species: str
    coefficient_parameter: str
    name: str
    output_channel: str = "log_intensity"
    requires: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        source = str(self.source_species).strip()
        parameter = str(self.coefficient_parameter).strip()
        name = str(self.name).strip()
        if not source or not parameter or not name:
            raise ValueError(
                "source_species, coefficient_parameter, and name must be non-empty"
            )
        object.__setattr__(self, "source_species", source)
        object.__setattr__(self, "coefficient_parameter", parameter)
        object.__setattr__(self, "name", name)

    @property
    def latent_species_dependencies(self) -> frozenset[str]:
        return frozenset({self.source_species})

    def priors(self):
        return {
            self.coefficient_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        }

    def _source_scalar(self, ctx, latent_fields):
        if latent_fields is None:
            raise RuntimeError("partner effect requires latent_fields")
        if self.source_species not in latent_fields.log_intensity:
            raise RuntimeError(
                f"source latent field {self.source_species!r} is unavailable"
            )
        return latent_fields.log_intensity[self.source_species][ctx.key]

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        pressure = _softplus_scalar(
            self._source_scalar(ctx, latent_fields)
        )
        return ProcessContribution(
            self.output_channel,
            theta[self.coefficient_parameter] * pressure,
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
        if latent_fields is None:
            raise RuntimeError("partner effect requires latent_fields")
        if self.source_species not in latent_fields.log_intensity:
            raise RuntimeError(
                f"source latent field {self.source_species!r} is unavailable"
            )
        source = latent_fields.log_intensity[self.source_species]
        if tuple(source.keys) != tuple(keys):
            raise RuntimeError("partner latent field context order mismatch")
        zero = array_module.asarray(0.0)
        pressure = array_module.logaddexp(zero, source.values)
        return ProcessContribution(
            self.output_channel,
            theta[self.coefficient_parameter] * pressure,
        )

    def knockout(self) -> NeutralPartnerIntensityEffect:
        return NeutralPartnerIntensityEffect(
            source_species=self.source_species,
            name=self.name,
        )
