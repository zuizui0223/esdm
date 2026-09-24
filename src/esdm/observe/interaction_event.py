"""Direct interaction-event count stream from paired latent ecological fields."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from esdm.process.base import PriorSpec
from .blocks import PoissonObservationBlock


_REQUIRED_TARGET_CHANNELS = frozenset({"log_intensity"})
_REQUIRED_SOURCE_CHANNELS = frozenset({"log_intensity"})


def _sigmoid_scalar(value) -> float:
    numeric = float(value)
    if numeric >= 0.0:
        z = math.exp(-numeric)
        return 1.0 / (1.0 + z)
    z = math.exp(numeric)
    return z / (1.0 + z)


@dataclass(frozen=True, slots=True)
class InteractionEventCount:
    """Poisson counts of directly observed source->target interaction events.

    The expected event count in one context is

        source latent abundance
        × target latent abundance
        × conditional event probability
        × observation effort
        × detection.

    The event probability is a stream-specific parameter and is intentionally distinct
    from a distributional PartnerIntensityEffect coefficient.  This keeps the direct
    event endpoint as independent evidence rather than silently reusing the same
    ecological parameter twice.
    """

    name: str
    source_species: str
    effort: object
    detection: object
    event_logit_parameter: str
    informs: frozenset[str]
    targets: frozenset[str] | None = None
    consumes: frozenset[str] = _REQUIRED_TARGET_CHANNELS
    required_latent_channels: frozenset[str] = _REQUIRED_TARGET_CHANNELS
    required_source_latent_channels: frozenset[str] = _REQUIRED_SOURCE_CHANNELS

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        source = str(self.source_species).strip()
        parameter = str(self.event_logit_parameter).strip()
        if not name or not source or not parameter:
            raise ValueError(
                "name, source_species, and event_logit_parameter must be non-empty"
            )
        if not hasattr(self.effort, "at") or not hasattr(self.effort, "array"):
            raise TypeError("effort must provide at(...) and array(...)")
        if not hasattr(self.effort, "priors"):
            raise TypeError("effort must provide priors()")
        if not hasattr(self.detection, "probability") or not hasattr(
            self.detection, "priors"
        ):
            raise TypeError("detection must provide probability(...) and priors()")
        if self.targets is None:
            raise ValueError("targets must be declared explicitly")
        targets = frozenset(str(value).strip() for value in self.targets)
        if len(targets) != 1 or any(not value for value in targets):
            raise ValueError(
                "interaction-event stream requires exactly one non-empty target species"
            )
        target = next(iter(targets))
        if target == source:
            raise ValueError("interaction-event source and target species must differ")

        event_prior_names = {parameter}
        overlap = (
            event_prior_names
            & (
                set(self.effort.priors())
                | set(self.detection.priors())
            )
        )
        if overlap:
            raise ValueError(
                f"interaction-event parameter names overlap: {sorted(overlap)}"
            )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "source_species", source)
        object.__setattr__(self, "event_logit_parameter", parameter)
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "informs", frozenset(str(x) for x in self.informs))
        object.__setattr__(self, "consumes", _REQUIRED_TARGET_CHANNELS)
        object.__setattr__(
            self,
            "required_latent_channels",
            _REQUIRED_TARGET_CHANNELS,
        )
        object.__setattr__(
            self,
            "required_source_latent_channels",
            _REQUIRED_SOURCE_CHANNELS,
        )

    @property
    def requires(self) -> frozenset[str]:
        return (
            frozenset(getattr(self.effort, "requires", frozenset()))
            | frozenset(getattr(self.detection, "requires", frozenset()))
        )

    def priors(self):
        effort = dict(self.effort.priors())
        detection = dict(self.detection.priors())
        overlap = set(effort) & set(detection)
        if overlap:
            raise ValueError(
                f"observation parameter names overlap: {sorted(overlap)}"
            )
        parameter = self.event_logit_parameter
        if parameter in effort or parameter in detection:
            raise ValueError(
                f"interaction-event parameter {parameter!r} overlaps another "
                "observation parameter"
            )
        return {
            **effort,
            **detection,
            parameter: PriorSpec("Normal", {"loc": 0.0, "scale": 2.0}),
        }

    def event_probability(self, theta_obs, *, array_module=None):
        if self.event_logit_parameter not in theta_obs:
            raise KeyError(
                f"missing event parameter {self.event_logit_parameter!r}"
            )
        value = theta_obs[self.event_logit_parameter]
        if array_module is None:
            return _sigmoid_scalar(value)
        return 1.0 / (1.0 + array_module.exp(-value))

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        keys = tuple(keys)
        detector = getattr(self.detection, "structural_exposure", None)
        if detector is not None and not bool(detector()):
            return tuple(False for _ in keys)
        mask_fn = getattr(self.effort, "structural_exposure_mask", None)
        if mask_fn is None:
            return tuple(True for _ in keys)
        mask = tuple(bool(value) for value in mask_fn(keys))
        if len(mask) != len(keys):
            raise ValueError("effort structural exposure mask must match context count")
        return mask

    def _validate_fields(self, species, fields):
        if species not in fields.log_intensity:
            raise ValueError(
                f"target species {species!r} has no latent log-intensity field"
            )
        if self.source_species not in fields.log_intensity:
            raise ValueError(
                f"source species {self.source_species!r} has no latent "
                "log-intensity field"
            )

    def validate_species_data(self, species, data, keys) -> None:
        keys = tuple(keys)
        unknown = set(data) - set(keys)
        if unknown:
            raise ValueError(
                f"interaction-event counts contain contexts outside the model domain"
            )
        values = tuple(int(data.get(key, 0)) for key in keys)
        if any(value < 0 for value in values):
            raise ValueError("interaction-event counts must be non-negative")
        mask = self.structural_exposure_mask(keys)
        impossible = [
            key
            for key, exposed, value in zip(keys, mask, values, strict=True)
            if not exposed and value > 0
        ]
        if impossible:
            raise ValueError(
                "positive interaction-event count in zero-exposure context: "
                f"{impossible[0]!r}"
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
        self._validate_fields(species, fields)
        obs = {} if theta_obs is None else theta_obs
        cov = {} if covariates is None else covariates

        if array_module is None:
            source = fields.log_intensity[self.source_species]
            target = fields.log_intensity[species]
            keys = tuple(target)
            if tuple(source) != keys:
                raise ValueError(
                    "interaction-event source/target context orders must match"
                )
            detection = self.detection.probability(obs)
            event_probability = self.event_probability(obs)
            rates = []
            for key in keys:
                effort = self.effort.at(
                    key,
                    theta=obs,
                    covariates=cov,
                )
                rates.append(
                    math.exp(float(source[key]))
                    * math.exp(float(target[key]))
                    * event_probability
                    * effort
                    * detection
                )
            rates = tuple(rates)
        else:
            source = fields.log_intensity[self.source_species]
            target = fields.log_intensity[species]
            keys = target.keys
            if source.keys != keys:
                raise ValueError(
                    "interaction-event source/target context orders must match"
                )
            effort = self.effort.array(
                keys,
                theta=obs,
                covariates=cov,
                array_module=array_module,
            )
            detection = self.detection.probability(
                obs,
                array_module=array_module,
            )
            event_probability = self.event_probability(
                obs,
                array_module=array_module,
            )
            rates = (
                array_module.exp(source.values)
                * array_module.exp(target.values)
                * event_probability
                * effort
                * detection
            )

        observed = None
        if data is not None:
            self.validate_species_data(species, data, keys)
            observed = tuple(int(data.get(key, 0)) for key in keys)

        return (
            PoissonObservationBlock(
                name=f"{self.name}.{self.source_species}->{species}",
                keys=keys,
                rates=rates,
                observed=observed,
                structural_exposure_mask=self.structural_exposure_mask(keys),
            ),
        )

    def log_lik(
        self,
        species,
        fields,
        counts,
        *,
        theta_obs=None,
        covariates=None,
    ) -> float:
        block = self.observation_blocks(
            species,
            fields,
            data=counts,
            theta_obs=theta_obs,
            covariates=covariates,
        )[0]
        total = 0.0
        for count, rate in zip(block.observed, block.rates, strict=True):
            numeric = float(rate)
            if numeric == 0.0:
                if count > 0:
                    return -math.inf
                continue
            total += (
                count * math.log(numeric)
                - numeric
                - math.lgamma(count + 1.0)
            )
        return total
