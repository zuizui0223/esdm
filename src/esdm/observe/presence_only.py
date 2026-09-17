"""Poisson presence-only observation stream with explicit effort and target taxa."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import math


@dataclass(frozen=True, slots=True)
class PresenceOnly:
    name: str
    effort: object
    informs: frozenset[str]
    detection_probability: float = 1.0
    consumes: frozenset[str] = frozenset({"log_intensity"})
    targets: frozenset[str] | None = None

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("stream name must be non-empty")
        p = float(self.detection_probability)
        if not math.isfinite(p) or p < 0.0 or p > 1.0:
            raise ValueError("detection_probability must be in [0, 1]")
        if not hasattr(self.effort, "at") or not hasattr(self.effort, "priors"):
            raise TypeError("effort must provide at(...) and priors()")
        if self.targets is None:
            raise ValueError("targets must be declared explicitly")
        targets = frozenset(str(value).strip() for value in self.targets)
        if not targets or any(not value for value in targets):
            raise ValueError("targets must be a non-empty set of species names")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "detection_probability", p)
        object.__setattr__(self, "informs", frozenset(str(x) for x in self.informs))
        object.__setattr__(self, "targets", targets)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(getattr(self.effort, "requires", frozenset()))

    def priors(self):
        return dict(self.effort.priors())

    def expected_rates(
        self,
        species: str,
        fields,
        *,
        theta_obs: Mapping[str, object] | None = None,
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]] | None = None,
        exp_fn=math.exp,
    ):
        """Return expected record rates using ecological and observation processes.

        There is no Python branch on the possibly inferred effort value, so this same
        implementation remains valid for ordinary scalars and JAX tracer values.
        """

        obs_parameters = {} if theta_obs is None else theta_obs
        observation_covariates = {} if covariates is None else covariates
        rates: dict[tuple[str, int, int], object] = {}
        if self.detection_probability == 0.0:
            return {
                key: 0.0 for key in fields.log_intensity[species]
            }
        for key, log_ecological in fields.log_intensity[species].items():
            effort = self.effort.at(
                key,
                theta=obs_parameters,
                covariates=observation_covariates,
                exp_fn=exp_fn,
            )
            rates[key] = (
                exp_fn(log_ecological)
                * effort
                * self.detection_probability
            )
        return rates

    def log_lik(
        self,
        species: str,
        fields,
        counts: Mapping[tuple[str, int, int], int],
        *,
        theta_obs: Mapping[str, object] | None = None,
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]] | None = None,
    ) -> float:
        rates = self.expected_rates(
            species,
            fields,
            theta_obs=theta_obs,
            covariates=covariates,
        )
        total = 0.0
        for key, rate in rates.items():
            count = int(counts.get(key, 0))
            if count < 0:
                raise ValueError("presence-only counts must be non-negative")
            numeric_rate = float(rate)
            if numeric_rate == 0.0:
                if count > 0:
                    return -math.inf
                continue
            total += count * math.log(numeric_rate) - numeric_rate - math.lgamma(count + 1.0)
        unknown = set(counts) - set(rates)
        if unknown:
            raise ValueError("counts contain contexts outside the latent field")
        return total
