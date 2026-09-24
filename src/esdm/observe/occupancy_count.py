"""Direct Poisson calibration of latent occupancy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from .blocks import PoissonObservationBlock


@dataclass(frozen=True, slots=True)
class OccupancyCount:
    """Direct occupancy observations independent of habitat suitability intensity."""

    name: str
    effort: object
    informs: frozenset[str]
    detection_probability: float = 1.0
    detection: object | None = None
    consumes: frozenset[str] = frozenset({"occupancy"})
    required_latent_channels: frozenset[str] = frozenset({"occupancy"})
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
        if self.detection is not None:
            if p != 1.0:
                raise ValueError(
                    "detection_probability must remain at 1.0 "
                    "when an explicit detection model is supplied"
                )
            if not hasattr(self.detection, "probability") or not hasattr(
                self.detection, "priors"
            ):
                raise TypeError(
                    "detection must provide probability(...) and priors()"
                )
            overlap = set(self.effort.priors()) & set(self.detection.priors())
            if overlap:
                raise ValueError(
                    f"observation parameter names overlap: {sorted(overlap)}"
                )
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
        effort_requires = frozenset(getattr(self.effort, "requires", frozenset()))
        detection_requires = (
            frozenset()
            if self.detection is None
            else frozenset(getattr(self.detection, "requires", frozenset()))
        )
        return effort_requires | detection_requires

    def priors(self):
        effort_priors = dict(self.effort.priors())
        if self.detection is None:
            return effort_priors
        detection_priors = dict(self.detection.priors())
        overlap = set(effort_priors) & set(detection_priors)
        if overlap:
            raise ValueError(
                f"observation parameter names overlap: {sorted(overlap)}"
            )
        return {**effort_priors, **detection_priors}

    def _detection_value(self, theta_obs, *, array_module=None):
        if self.detection is None:
            return self.detection_probability
        return self.detection.probability(
            theta_obs,
            array_module=array_module,
        )

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        keys = tuple(keys)
        if self.detection is None:
            if self.detection_probability == 0.0:
                return tuple(False for _ in keys)
        else:
            exposure_fn = getattr(self.detection, "structural_exposure", None)
            if exposure_fn is not None and not bool(exposure_fn()):
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
    ):
        if species not in fields.occupancy:
            raise ValueError(
                f"species {species!r} lacks an occupancy latent field"
            )
        obs = {} if theta_obs is None else theta_obs
        covs = {} if covariates is None else covariates
        detection = self._detection_value(obs)
        rates = {}
        for key, occupancy in fields.occupancy[species].items():
            effort = self.effort.at(
                key,
                theta=obs,
                covariates=covs,
            )
            rates[key] = occupancy * effort * detection
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

        if species not in fields.occupancy:
            raise ValueError(
                f"species {species!r} lacks an occupancy latent field"
            )
        occupancy = fields.occupancy[species]
        obs = {} if theta_obs is None else theta_obs
        covs = {} if covariates is None else covariates
        effort = self.effort.array(
            occupancy.keys,
            theta=obs,
            covariates=covs,
            array_module=array_module,
        )
        detection = self._detection_value(obs, array_module=array_module)
        return ContextArray(
            occupancy.keys,
            occupancy.values * effort * detection,
        )

    def validate_species_data(self, species, data, keys) -> None:
        keys = tuple(keys)
        unknown = set(data) - set(keys)
        if unknown:
            raise ValueError(
                f"data for {self.name}:{species} contain contexts outside the model domain"
            )
        values = tuple(int(data.get(key, 0)) for key in keys)
        if any(value < 0 for value in values):
            raise ValueError("occupancy counts must be non-negative")
        mask = self.structural_exposure_mask(keys)
        impossible = [
            key
            for key, exposed, value in zip(keys, mask, values, strict=True)
            if not exposed and value > 0
        ]
        if impossible:
            raise ValueError(
                f"positive count in zero-exposure context for "
                f"{self.name}:{species}: {impossible[0]!r}"
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
                raise ValueError("occupancy counts must be non-negative")
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
