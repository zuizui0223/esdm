"""In-model simulation using the same latent fields and observation rates as likelihoods."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
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


def simulate_presence_only(model, theta, covariates, *, seed: int) -> GeneratedPresenceOnly:
    """Generate counts through the exact same `expected_rates` path used by likelihoods."""

    model.check_design()
    fields = model.latent_fields(theta, covariates)
    rng = random.Random(int(seed))
    counts: dict[str, dict[str, dict[tuple[str, int, int], int]]] = {}
    expected: dict[str, dict[str, dict[tuple[str, int, int], float]]] = {}

    for stream in model.streams:
        if not isinstance(stream, PresenceOnly):
            continue
        counts[stream.name] = {}
        expected[stream.name] = {}
        for species in model.species:
            rates = stream.expected_rates(species, fields)
            expected[stream.name][species] = dict(rates)
            counts[stream.name][species] = {
                key: _poisson(rng, rate) for key, rate in rates.items()
            }

    return GeneratedPresenceOnly(counts=counts, expected_rates=expected)
