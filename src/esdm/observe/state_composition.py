"""Direct state-composition calibration observation stream."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from esdm.domain import StateSpace

from .blocks import PoissonObservationBlock


_REQUIRED_CHANNELS = frozenset({"state"})


@dataclass(frozen=True, slots=True)
class StateCompositionCount:
    """Poissonized conditional state labels with fixed expected label effort.

    The stream consumes only the latent state-composition channel.  For context c and
    state s its expected count is

        label_effort[c] * P(state=s | active, available, c)

    so the total expected number of labels at an exposed context is exactly the declared
    label effort and is independent of ecological intensity and activity.
    """

    name: str
    state_space: StateSpace
    effort: object
    informs: frozenset[str]
    targets: frozenset[str] | None = None
    consumes: frozenset[str] = _REQUIRED_CHANNELS
    required_latent_channels: frozenset[str] = _REQUIRED_CHANNELS

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("stream name must be non-empty")
        if not isinstance(self.state_space, StateSpace):
            raise TypeError("state_space must be a StateSpace")
        if not hasattr(self.effort, "at") or not hasattr(self.effort, "array"):
            raise TypeError("effort must provide at(...) and array(...)")
        if not hasattr(self.effort, "priors"):
            raise TypeError("effort must provide priors()")
        if self.targets is None:
            raise ValueError("targets must be declared explicitly")
        targets = frozenset(str(value).strip() for value in self.targets)
        if not targets or any(not value for value in targets):
            raise ValueError("targets must be a non-empty set of species names")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "informs", frozenset(str(x) for x in self.informs))
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "consumes", _REQUIRED_CHANNELS)
        object.__setattr__(self, "required_latent_channels", _REQUIRED_CHANNELS)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(getattr(self.effort, "requires", frozenset()))

    def priors(self):
        return dict(self.effort.priors())

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        keys = tuple(keys)
        mask_fn = getattr(self.effort, "structural_exposure_mask", None)
        if mask_fn is None:
            return tuple(True for _ in keys)
        mask = tuple(bool(value) for value in mask_fn(keys))
        if len(mask) != len(keys):
            raise ValueError("effort structural exposure mask must match context count")
        return mask

    def _validate_state_labels(self, labels) -> tuple[str, ...]:
        labels = tuple(labels)
        if labels != self.state_space.states:
            raise ValueError("latent state labels must match the stream state space")
        return labels

    def _validate_observed(self, data, keys, mask):
        if data is None:
            return {state: None for state in self.state_space.states}
        if set(data) != set(self.state_space.states):
            raise ValueError("composition data state labels must match state_space exactly")
        output = {}
        key_set = set(keys)
        for state in self.state_space.states:
            counts = data[state]
            unknown = set(counts) - key_set
            if unknown:
                raise ValueError(
                    "composition counts contain contexts outside the latent field"
                )
            values = tuple(int(counts.get(key, 0)) for key in keys)
            if any(value < 0 for value in values):
                raise ValueError("composition counts must be non-negative")
            impossible = [
                key
                for key, exposed, value in zip(keys, mask, values, strict=True)
                if not exposed and value > 0
            ]
            if impossible:
                raise ValueError(
                    "positive composition count in zero-exposure context: "
                    f"{impossible[0]!r}"
                )
            output[state] = values
        return output

    def validate_species_data(self, species, data, keys) -> None:
        keys = tuple(keys)
        self._validate_observed(
            data,
            keys,
            self.structural_exposure_mask(keys),
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
        obs_parameters = {} if theta_obs is None else theta_obs
        observation_covariates = {} if covariates is None else covariates

        if species not in fields.state_probabilities:
            raise ValueError(f"species {species!r} has no state probability field")

        if array_module is None:
            state_field = fields.state_probabilities[species]
            labels = self._validate_state_labels(fields.state_labels[species])
            keys = tuple(state_field)
            rates_by_state = {state: [] for state in labels}
            for key in keys:
                effort = self.effort.at(
                    key,
                    theta=obs_parameters,
                    covariates=observation_covariates,
                )
                for index, state in enumerate(labels):
                    rates_by_state[state].append(
                        effort * float(state_field[key][index])
                    )
            rates_by_state = {
                state: tuple(values)
                for state, values in rates_by_state.items()
            }
        else:
            state_field = fields.state_probabilities[species]
            labels = self._validate_state_labels(state_field.states)
            keys = state_field.keys
            effort = self.effort.array(
                keys,
                theta=obs_parameters,
                covariates=observation_covariates,
                array_module=array_module,
            )
            rates_by_state = {
                state: effort * state_field.values[:, index]
                for index, state in enumerate(labels)
            }

        mask = self.structural_exposure_mask(keys)
        observed = self._validate_observed(data, keys, mask)
        return tuple(
            PoissonObservationBlock(
                name=f"{self.name}.{species}.{state}",
                keys=keys,
                rates=rates_by_state[state],
                observed=observed[state],
                structural_exposure_mask=mask,
            )
            for state in labels
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
        total = 0.0
        blocks = self.observation_blocks(
            species,
            fields,
            data=counts,
            theta_obs=theta_obs,
            covariates=covariates,
        )
        for block in blocks:
            for count, rate in zip(block.observed, block.rates, strict=True):
                numeric_rate = float(rate)
                if numeric_rate < 0.0 or not math.isfinite(numeric_rate):
                    raise ValueError(
                        "composition Poisson rates must be finite and non-negative"
                    )
                if numeric_rate == 0.0:
                    if count > 0:
                        return -math.inf
                    continue
                total += (
                    count * math.log(numeric_rate)
                    - numeric_rate
                    - math.lgamma(count + 1.0)
                )
        return total
