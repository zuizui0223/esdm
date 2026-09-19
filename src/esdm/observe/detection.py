"""Detection models for observation streams."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.process.base import PriorSpec


@dataclass(frozen=True, slots=True)
class KnownDetection:
    value: float

    def __post_init__(self) -> None:
        value = float(self.value)
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise ValueError("known detection probability must be in [0, 1]")
        object.__setattr__(self, "value", value)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset()

    def priors(self) -> dict[str, PriorSpec]:
        return {}

    def probability(self, theta=None, *, array_module=None):
        return self.value

    def structural_exposure(self) -> bool:
        return self.value > 0.0


@dataclass(frozen=True, slots=True)
class LogitDetection:
    intercept_parameter: str = "detection_intercept"

    def __post_init__(self) -> None:
        parameter = str(self.intercept_parameter).strip()
        if not parameter:
            raise ValueError("detection intercept parameter must be non-empty")
        object.__setattr__(self, "intercept_parameter", parameter)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset()

    def priors(self) -> dict[str, PriorSpec]:
        return {
            self.intercept_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 2.0}
            )
        }

    def probability(self, theta, *, array_module=None):
        if self.intercept_parameter not in theta:
            raise KeyError(
                f"missing detection parameter {self.intercept_parameter!r}"
            )
        value = theta[self.intercept_parameter]
        if array_module is None:
            numeric = float(value)
            if numeric >= 0.0:
                z = math.exp(-numeric)
                return 1.0 / (1.0 + z)
            z = math.exp(numeric)
            return z / (1.0 + z)
        return 1.0 / (1.0 + array_module.exp(-value))

    def structural_exposure(self) -> bool:
        return True
