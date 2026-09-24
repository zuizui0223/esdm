"""Poisson pair-event observation stream over two latent species fields."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import math

from esdm.process.base import PriorSpec
from .blocks import PoissonObservationBlock


def _softplus(value) -> float:
    numeric = float(value)
    if numeric > 0.0:
        return numeric + math.log1p(math.exp(-numeric))
    return math.log1p(math.exp(numeric))


@dataclass(frozen=True, slots=True)
class PairEventCount:
    """Observed directed source->target event counts.

    The stream is a realized-event endpoint, not a causal-effect process. Its expected
    rate is proportional to observation effort, a pair-specific event-rate parameter,
    and positive availability proxies derived from source and target latent ecological
    intensities.
    """

    name: str
    source_species: str
    target_species: str
    effort: object
    event_intercept_parameter: str
    informs: frozenset[str]
    consumes: frozenset[str] = frozenset({"log_intensity"})
    required_latent_channels: frozenset[str] = frozenset({"log_intensity"})
    targets: frozenset[str] = field(init=False)

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        source = str(self.source_species).strip()
        target = str(self.target_species).strip()
        parameter = str(self.event_intercept_parameter).strip()
        if not name or not source or not target or not parameter:
            raise ValueError(
                "name, source_species, target_species, and event parameter must be non-empty"
            )
        if source == target:
            raise ValueError("pair-event source and target must differ")
        if not hasattr(self.effort, "at") or not hasattr(self.effort, "array"):
            raise TypeError("effort must provide at(...) and array(...)")
        if not hasattr(self.effort, "priors"):
            raise TypeError("effort must provide priors()")
        if parameter in self.effort.priors():
            raise ValueError("event-rate parameter overlaps effort parameter")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "source_species", source)
        object.__setattr__(self, "target_species", target)
        object.__setattr__(self, "event_intercept_parameter", parameter)
        object.__setattr__(self, "informs", frozenset(str(x) for x in self.informs))
        object.__setattr__(self, "targets", frozenset({target}))

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(getattr(self.effort, "requires", frozenset()))

    def priors(self):
        effort_priors = dict(self.effort.priors())
        return {
            **effort_priors,
            self.event_intercept_parameter: PriorSpec(
                "Normal", {"loc": -2.0, "scale": 1.0}
            ),
        }

    def validate_model(self, model) -> None:
        known = set(model.species)
        if self.source_species not in known:
            raise ValueError(
                f"pair-event stream {self.name!r} has unknown source species "
                f"{self.source_species!r}"
            )
        if self.target_species not in known:
            raise ValueError(
                f"pair-event stream {self.name!r} has unknown target species "
                f"{self.target_species!r}"
            )
        for species in (self.source_species, self.target_species):
            available = {
                str(process.output_channel)
                for process in model.species[species]
            }
            if "log_intensity" not in available:
                raise ValueError(
                    f"pair-event species {species!r} lacks log_intensity process"
                )

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        keys = tuple(keys)
        mask_fn = getattr(self.effort, "structural_exposure_mask", None)
        if mask_fn is None:
            return tuple(True for _ in keys)
        mask = tuple(bool(value) for value in mask_fn(keys))
        if len(mask) != len(keys):
            raise ValueError("effort structural exposure mask must match context count")
        return mask

    def _event_scale(self, theta_obs, *, exp_fn=math.exp):
        if self.event_intercept_parameter not in theta_obs:
            raise KeyError(
                f"missing pair-event parameter {self.event_intercept_parameter!r}"
            )
        return exp_fn(theta_obs[self.event_intercept_parameter])

    def expected_rates(
        self,
        species: str,
        fields,
        *,
        theta_obs: Mapping[str, object] | None = None,
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]] | None = None,
    ):
        if species != self.target_species:
            raise ValueError("PairEventCount can only be evaluated for its target species")
        if self.source_species not in fields.log_intensity:
            raise ValueError("source latent field is unavailable")
        if self.target_species not in fields.log_intensity:
            raise ValueError("target latent field is unavailable")
        obs = {} if theta_obs is None else theta_obs
        covs = {} if covariates is None else covariates
        scale = self._event_scale(obs)
        source = fields.log_intensity[self.source_species]
        target = fields.log_intensity[self.target_species]
        if tuple(source) != tuple(target):
            raise ValueError("source and target latent contexts must match")

        rates = {}
        for key in source:
            effort = self.effort.at(
                key,
                theta=obs,
                covariates=covs,
            )
            rates[key] = (
                effort
                * scale
                * _softplus(source[key])
                * _softplus(target[key])
            )
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
        from esdm.model.arrays import ContextArray

        if species != self.target_species:
            raise ValueError("PairEventCount can only be evaluated for its target species")
        source = fields.log_intensity[self.source_species]
        target = fields.log_intensity[self.target_species]
        if source.keys != target.keys:
            raise ValueError("source and target latent context orders must match")
        obs = {} if theta_obs is None else theta_obs
        covs = {} if covariates is None else covariates
        if self.event_intercept_parameter not in obs:
            raise KeyError(
                f"missing pair-event parameter {self.event_intercept_parameter!r}"
            )
        effort = self.effort.array(
            source.keys,
            theta=obs,
            covariates=covs,
            array_module=array_module,
        )
        zero = array_module.asarray(0.0)
        source_pressure = array_module.logaddexp(zero, source.values)
        target_pressure = array_module.logaddexp(zero, target.values)
        scale = array_module.exp(obs[self.event_intercept_parameter])
        return ContextArray(
            source.keys,
            effort * scale * source_pressure * target_pressure,
        )

    def validate_species_data(self, species, data, keys) -> None:
        if species != self.target_species:
            raise ValueError("PairEventCount data species must equal target_species")
        keys = tuple(keys)
        unknown = set(data) - set(keys)
        if unknown:
            raise ValueError("pair-event counts contain contexts outside the model domain")
        values = tuple(int(data.get(key, 0)) for key in keys)
        if any(value < 0 for value in values):
            raise ValueError("pair-event counts must be non-negative")
        mask = self.structural_exposure_mask(keys)
        impossible = [
            key
            for key, exposed, value in zip(keys, mask, values, strict=True)
            if not exposed and value > 0
        ]
        if impossible:
            raise ValueError(
                f"positive pair-event count in zero-exposure context: {impossible[0]!r}"
            )

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
            self.validate_species_data(species, data, keys)
            observed = tuple(int(data.get(key, 0)) for key in keys)

        return (
            PoissonObservationBlock(
                name=f"{self.name}.{self.source_species}_to_{self.target_species}",
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
        counts,
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
                raise ValueError("pair-event counts must be non-negative")
            numeric_rate = float(rate)
            if numeric_rate == 0.0:
                if count > 0:
                    return -math.inf
                continue
            total += (
                count * math.log(numeric_rate)
                - numeric_rate
                - math.lgamma(count + 1.0)
            )
        unknown = set(counts) - set(rates)
        if unknown:
            raise ValueError("pair-event counts contain contexts outside the latent field")
        return total
