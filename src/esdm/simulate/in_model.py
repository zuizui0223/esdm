"""In-model simulation using the same latent fields and observation rates as likelihoods."""

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
class GeneratedPresenceOnly:
    counts: dict[str, dict[str, dict[tuple[str, int, int], int]]]
    expected_rates: dict[str, dict[str, dict[tuple[str, int, int], float]]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "counts", dict(self.counts))
        object.__setattr__(self, "expected_rates", dict(self.expected_rates))


def simulate_presence_only(
    model,
    theta,
    covariates,
    *,
    seed: int,
    theta_obs=None,
) -> GeneratedPresenceOnly:
    """Generate counts through the exact same process/stream path used by likelihoods."""

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
    counts: dict[str, dict[str, dict[tuple[str, int, int], int]]] = {}
    expected: dict[str, dict[str, dict[tuple[str, int, int], float]]] = {}

    for stream in model.streams:
        if not isinstance(stream, PresenceOnly):
            continue
        stream_theta = dict(observation_parameters.get(stream.name, {}))
        required = set(stream.priors())
        missing = required - set(stream_theta)
        if missing:
            raise KeyError(
                f"stream {stream.name!r} missing observation parameters: {sorted(missing)}"
            )
        unexpected = set(stream_theta) - required
        if unexpected:
            raise KeyError(
                f"stream {stream.name!r} received undeclared observation parameters: "
                f"{sorted(unexpected)}"
            )
        counts[stream.name] = {}
        expected[stream.name] = {}
        for species in model.stream_targets(stream):
            rates = stream.expected_rates(
                species,
                fields,
                theta_obs=stream_theta,
                covariates=covariates,
            )
            expected[stream.name][species] = dict(rates)
            counts[stream.name][species] = {
                key: _poisson(rng, rate) for key, rate in rates.items()
            }

    return GeneratedPresenceOnly(counts=counts, expected_rates=expected)
