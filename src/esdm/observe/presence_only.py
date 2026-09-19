"""Poisson presence-only observation stream with explicit effort and target taxa."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from .blocks import PoissonObservationBlock


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

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        """Return statically known observation opportunities in key order."""

        keys = tuple(keys)
        if self.detection_probability == 0.0:
            return tuple(False for _ in keys)
        mask_fn = getattr(self.effort, "structural_exposure_mask", None)
        if mask_fn is None:
            return tuple(True for _ in keys)
        mask = tuple(bool(value) for value in mask_fn(keys))
        if len(mask) != len(keys):
            raise ValueError("effort structural exposure mask must match context count")
        return mask

    def expected_rates(
        self,
        species: str,
        fields,
        *,
        theta_obs: Mapping[str, object] | None = None,
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]] | None = None,
        exp_fn=math.exp,
    ):
        """Return expected record rates using ecological and observation processes."""

        obs_parameters = {} if theta_obs is None else theta_obs
        observation_covariates = {} if covariates is None else covariates
        rates: dict[tuple[str, int, int], object] = {}
        if self.detection_probability == 0.0:
            return {key: 0.0 for key in fields.log_intensity[species]}
        for key, log_ecological in fields.log_intensity[species].items():
            effort = self.effort.at(
                key,
                theta=obs_parameters,
                covariates=observation_covariates,
                exp_fn=exp_fn,
            )
            rates[key] = exp_fn(log_ecological) * effort * self.detection_probability
        return rates

    def expected_rate_array(
        self,
        species: str,
        fields,
        *,
        theta_obs: Mapping[str, object] | None = None,
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]] | None = None,
        array_module,
    ):
        """Return one vectorized expected-rate array in latent-field key order."""

        from esdm.model.arrays import ContextArray

        field = fields.log_intensity[species]
        if self.detection_probability == 0.0:
            return ContextArray(field.keys, array_module.zeros_like(field.values))
        obs_parameters = {} if theta_obs is None else theta_obs
        observation_covariates = {} if covariates is None else covariates
        effort = self.effort.array(
            field.keys,
            theta=obs_parameters,
            covariates=observation_covariates,
            array_module=array_module,
        )
        values = array_module.exp(field.values) * effort * self.detection_probability
        return ContextArray(field.keys, values)

    def observation_blocks(
        self,
        species: str,
        fields,
        *,
        data=None,
        theta_obs: Mapping[str, object] | None = None,
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]] | None = None,
        array_module=None,
    ):
        """Expose this stream as one backend-neutral Poisson block."""

        if array_module is None:
            rate_map = self.expected_rates(
                species,
                fields,
                theta_obs=theta_obs,
                covariates=covariates,
            )
            keys = tuple(rate_map)
            rates = tuple(rate_map[key] for key in keys)
        else:
            rate_array = self.expected_rate_array(
                species,
                fields,
                theta_obs=theta_obs,
                covariates=covariates,
                array_module=array_module,
            )
            keys = rate_array.keys
            rates = rate_array.values

        observed = None
        if data is not None:
            unknown = set(data) - set(keys)
            if unknown:
                raise ValueError("counts contain contexts outside the latent field")
            observed_values = tuple(int(data.get(key, 0)) for key in keys)
            if any(value < 0 for value in observed_values):
                raise ValueError("presence-only counts must be non-negative")
            observed = observed_values

        return (
            PoissonObservationBlock(
                name=f"{self.name}.{species}",
                keys=keys,
                rates=rates,
                observed=observed,
                structural_exposure_mask=self.structural_exposure_mask(keys),
            ),
        )

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
