"""Backend-neutral ecological process contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Mapping, Any

from esdm.domain import Context


@dataclass(frozen=True, slots=True)
class PriorSpec:
    distribution: str
    parameters: Mapping[str, float]


class Process(Protocol):
    name: str
    output_channel: str
    requires: frozenset[str]
    latent_species_dependencies: frozenset[str]
    knockout_semantics: str

    def priors(self) -> dict[str, PriorSpec]: ...

    def log_intensity(
        self,
        ctx: Context,
        theta: Mapping[str, float],
        covariates: Mapping[str, float],
        latent_fields: Any | None = None,
    ) -> float: ...

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

    def knockout(self) -> "NoEffectProcess":
        return self
