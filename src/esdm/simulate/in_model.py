"""In-model simulation through shared latent fields and observation blocks."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

from esdm.observe import PresenceOnly


def _poisson(rng: random.Random, rate: float) -> int:
    rate = float(rate)
    if not math.isfinite(rate) or rate < 0.0:
        raise ValueError("Poisson rate must be finite and non-negative")
    if rate == 0.0:
        return 0
    if rate > 20.0:
        parts = max(2, math.ceil(rate / 20.0))
        subrate = rate / parts
        return sum(_poisson(rng, subrate) for _ in range(parts))
    threshold = math.exp(-rate)
    product = 1.0
    count = 0
    while product > threshold:
        count += 1
        product *= rng.random()
    return count - 1


@dataclass(frozen=True, slots=True)
class GeneratedObservations:
    counts: dict
    expected_rates: dict

    def __post_init__(self) -> None:
        object.__setattr__(self, "counts", dict(self.counts))
        object.__setattr__(self, "expected_rates", dict(self.expected_rates))


@dataclass(frozen=True, slots=True)
class GeneratedPresenceOnly:
    counts: dict[str, dict[str, dict[tuple[str, int, int], int]]]
    expected_rates: dict[str, dict[str, dict[tuple[str, int, int], float]]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "counts", dict(self.counts))
        object.__setattr__(self, "expected_rates", dict(self.expected_rates))


def _stream_theta(stream, observation_parameters):
    parameters = dict(observation_parameters.get(stream.name, {}))
    required = set(stream.priors())
    missing = required - set(parameters)
    if missing:
        raise KeyError(
            f"stream {stream.name!r} missing observation parameters: {sorted(missing)}"
        )
    unexpected = set(parameters) - required
    if unexpected:
        raise KeyError(
            f"stream {stream.name!r} received undeclared observation parameters: "
            f"{sorted(unexpected)}"
        )
    return parameters


def _sample_block(rng, block):
    return {
        key: _poisson(rng, rate)
        for key, rate in zip(block.keys, block.rates, strict=True)
    }


def _expected_block(block):
    return {
        key: float(rate)
        for key, rate in zip(block.keys, block.rates, strict=True)
    }


def simulate_observations(
    model,
    theta,
    covariates,
    *,
    seed: int,
    theta_obs=None,
) -> GeneratedObservations:
    """Generate every declared stream through shared observation blocks."""

    model.check_design()
    fields = model.latent_fields(theta, covariates)
    observation_parameters = {} if theta_obs is None else dict(theta_obs)
    known_streams = {stream.name for stream in model.streams}
    unknown_streams = set(observation_parameters) - known_streams
    if unknown_streams:
        raise KeyError(
            f"observation parameters contain unknown streams: {sorted(unknown_streams)}"
        )

    rng = random.Random(int(seed))
    counts = {}
    expected = {}

    for stream in model.streams:
        stream_theta = _stream_theta(stream, observation_parameters)
        counts[stream.name] = {}
        expected[stream.name] = {}

        for species in model.stream_targets(stream):
            blocks = tuple(
                stream.observation_blocks(
                    species,
                    fields,
                    theta_obs=stream_theta,
                    covariates=covariates,
                )
            )
            if not blocks:
                raise ValueError(
                    f"stream {stream.name!r} produced no observation blocks"
                )

            state_space = getattr(stream, "state_space", None)
            if state_space is None:
                if len(blocks) != 1:
                    raise ValueError(
                        f"stream {stream.name!r} requires an explicit block packing contract"
                    )
                block = blocks[0]
                counts[stream.name][species] = _sample_block(rng, block)
                expected[stream.name][species] = _expected_block(block)
                continue

            labels = tuple(state_space.states)
            if len(blocks) != len(labels):
                raise ValueError(
                    f"stream {stream.name!r} observation block count does not match states"
                )
            counts[stream.name][species] = {}
            expected[stream.name][species] = {}
            for state, block in zip(labels, blocks, strict=True):
                expected_name = f"{stream.name}.{species}.{state}"
                if block.name != expected_name:
                    raise ValueError(
                        f"stream {stream.name!r} returned unexpected block name {block.name!r}"
                    )
                counts[stream.name][species][state] = _sample_block(rng, block)
                expected[stream.name][species][state] = _expected_block(block)

    return GeneratedObservations(counts=counts, expected_rates=expected)


def simulate_presence_only(
    model,
    theta,
    covariates,
    *,
    seed: int,
    theta_obs=None,
) -> GeneratedPresenceOnly:
    """Compatibility wrapper for models containing only PresenceOnly streams."""

    if any(not isinstance(stream, PresenceOnly) for stream in model.streams):
        raise TypeError(
            "simulate_presence_only requires every stream to be PresenceOnly"
        )
    generated = simulate_observations(
        model,
        theta,
        covariates,
        seed=seed,
        theta_obs=theta_obs,
    )
    return GeneratedPresenceOnly(
        counts=generated.counts,
        expected_rates=generated.expected_rates,
    )
