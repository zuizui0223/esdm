"""Observation-effort models, separate from ecological intensity."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math

from esdm.process.base import PriorSpec


@dataclass(frozen=True, slots=True)
class EffortField:
    """Known effort values over the observation domain."""

    values: Mapping[tuple[str, int, int], float]

    def __post_init__(self) -> None:
        cleaned: dict[tuple[str, int, int], float] = {}
        for key, value in self.values.items():
            if not isinstance(key, tuple) or len(key) != 3:
                raise ValueError("effort keys must be (space, doy, hour)")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0.0:
                raise ValueError("effort values must be finite and non-negative")
            cleaned[(str(key[0]), int(key[1]), int(key[2]))] = numeric
        object.__setattr__(self, "values", MappingProxyType(cleaned))

    @property
    def requires(self) -> frozenset[str]:
        return frozenset()

    def priors(self) -> dict[str, PriorSpec]:
        return {}

    def at(
        self,
        key: tuple[str, int, int],
        *,
        theta=None,
        covariates=None,
        exp_fn=math.exp,
    ) -> float:
        return float(self.values.get(key, 0.0))


@dataclass(frozen=True, slots=True)
class LogLinearEffort:
    """Unknown effort gradient estimated as part of the observation process.

    The baseline scale is known while the coefficient is inferred. This is sufficient
    to construct a genuine confounding benchmark where an ecological gradient and an
    observation-effort gradient act on the same covariate.
    """

    baseline: float
    covariate: str
    coefficient_parameter: str

    def __post_init__(self) -> None:
        baseline = float(self.baseline)
        covariate = str(self.covariate).strip()
        parameter = str(self.coefficient_parameter).strip()
        if not math.isfinite(baseline) or baseline <= 0.0:
            raise ValueError("baseline effort must be finite and positive")
        if not covariate or not parameter:
            raise ValueError("effort covariate and parameter names must be non-empty")
        object.__setattr__(self, "baseline", baseline)
        object.__setattr__(self, "covariate", covariate)
        object.__setattr__(self, "coefficient_parameter", parameter)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset({self.covariate})

    def priors(self) -> dict[str, PriorSpec]:
        return {
            self.coefficient_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        }

    def at(
        self,
        key: tuple[str, int, int],
        *,
        theta,
        covariates,
        exp_fn=math.exp,
    ):
        if self.coefficient_parameter not in theta:
            raise KeyError(
                f"missing observation-effort parameter {self.coefficient_parameter!r}"
            )
        if key not in covariates or self.covariate not in covariates[key]:
            raise KeyError(
                f"missing observation-effort covariate {self.covariate!r} for {key!r}"
            )
        return self.baseline * exp_fn(
            theta[self.coefficient_parameter] * covariates[key][self.covariate]
        )
