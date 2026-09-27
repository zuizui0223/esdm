"""Backend-neutral ecological process contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from esdm.domain import Context


@dataclass(frozen=True, slots=True)
class PriorSpec:
    distribution: str
    parameters: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class ProcessContribution:
    """One ecological process contribution to a semantic latent channel."""

    channel: str
    values: object
    labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        channel = str(self.channel).strip()
        labels = tuple(str(label).strip() for label in self.labels)
        if not channel:
            raise ValueError("contribution channel must be non-empty")
        if any(not label for label in labels) or len(set(labels)) != len(labels):
            raise ValueError("contribution labels must be unique non-empty strings")
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "labels", labels)


class Process(Protocol):
    name: str
    output_channel: str
    requires: frozenset[str]
    latent_species_dependencies: frozenset[str]
    knockout_semantics: str

    def priors(self) -> dict[str, PriorSpec]: ...

    def contribution(
        self,
        ctx: Context,
        theta: Mapping[str, float],
        covariates: Mapping[str, float],
        latent_fields: Any | None = None,
    ) -> ProcessContribution: ...

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields: Any | None = None,
    ) -> ProcessContribution: ...

    def knockout(self) -> "Process": ...


@dataclass(frozen=True, slots=True)
class NoEffectProcess:
    name: str
    output_channel: str = "log_intensity"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "no_effect_log_contribution_zero"

    def priors(self) -> dict[str, PriorSpec]:
        return {}

    def log_intensity(self, ctx, theta, covariates, latent_fields=None) -> float:
        return 0.0

    def log_intensity_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        return array_module.zeros((len(keys),))

    def contribution(self, ctx, theta, covariates, latent_fields=None) -> ProcessContribution:
        return ProcessContribution(
            self.output_channel,
            self.log_intensity(ctx, theta, covariates, latent_fields=latent_fields),
        )

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ) -> ProcessContribution:
        return ProcessContribution(
            self.output_channel,
            self.log_intensity_array(
                keys,
                theta,
                covariates,
                array_module=array_module,
                latent_fields=latent_fields,
            ),
        )

    def knockout(self) -> "NoEffectProcess":
        return self
