"""Poisson presence-only observation stream with explicit effort."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import math

from .effort import EffortField


@dataclass(frozen=True, slots=True)
class PresenceOnly:
    name: str
    effort: EffortField
    informs: frozenset[str]
    detection_probability: float = 1.0
    consumes: frozenset[str] = frozenset({"log_intensity"})

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("stream name must be non-empty")
        p = float(self.detection_probability)
        if not math.isfinite(p) or p < 0.0 or p > 1.0:
            raise ValueError("detection_probability must be in [0, 1]")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "detection_probability", p)
        object.__setattr__(self, "informs", frozenset(str(x) for x in self.informs))

    def expected_rates(self, species: str, fields, *, exp_fn=math.exp):
        """Return expected record rates using the observation-process contract.

        ``exp_fn`` defaults to :func:`math.exp`, but JAX/NumPyro can inject
        ``jax.numpy.exp``.  The ecological formula therefore lives in one place rather
        than being reimplemented by the inference backend.
        """

        rates: dict[tuple[str, int, int], object] = {}
        for key, log_ecological in fields.log_intensity[species].items():
            effort = self.effort.at(key)
            if effort == 0.0 or self.detection_probability == 0.0:
                rates[key] = 0.0
            else:
                rates[key] = exp_fn(log_ecological) * effort * self.detection_probability
        return rates

    def log_lik(
        self,
        species: str,
        fields,
        counts: Mapping[tuple[str, int, int], int],
    ) -> float:
        rates = self.expected_rates(species, fields)
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
