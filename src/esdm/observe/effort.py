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

    def array(
        self,
        keys,
        *,
        theta=None,
        covariates=None,
        array_module,
    ):
        return array_module.asarray([self.values.get(key, 0.0) for key in keys])

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        """Return contexts that can structurally generate records.

        Known zero effort is an absent observation opportunity, not a Poisson constraint
        at the boundary rate zero.
        """

        return tuple(float(self.values.get(key, 0.0)) > 0.0 for key in keys)


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

    def array(
        self,
        keys,
        *,
        theta,
        covariates,
        array_module,
    ):
        if self.coefficient_parameter not in theta:
            raise KeyError(
                f"missing observation-effort parameter {self.coefficient_parameter!r}"
            )
        missing = [
            key
            for key in keys
            if key not in covariates or self.covariate not in covariates[key]
        ]
        if missing:
            raise KeyError(
                f"missing observation-effort covariate {self.covariate!r} for {missing[0]!r}"
            )
        x = array_module.asarray([covariates[key][self.covariate] for key in keys])
        return self.baseline * array_module.exp(
            theta[self.coefficient_parameter] * x
        )

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        """Log-linear effort is strictly positive for every finite parameter value."""

        return tuple(True for _ in keys)



@dataclass(frozen=True, slots=True)
class MultiLogLinearEffort:
    """Unknown log-linear observation effort over multiple declared covariates."""

    baseline: float
    covariates: tuple[str, ...]
    coefficient_parameters: Mapping[str, str]

    def __post_init__(self) -> None:
        baseline = float(self.baseline)
        covariates = tuple(str(value).strip() for value in self.covariates)
        if not math.isfinite(baseline) or baseline <= 0.0:
            raise ValueError("baseline effort must be finite and positive")
        if not covariates or any(not value for value in covariates):
            raise ValueError("effort covariates must be non-empty")
        if len(set(covariates)) != len(covariates):
            raise ValueError("effort covariates must be unique")
        coefficients = {
            str(key).strip(): str(value).strip()
            for key, value in self.coefficient_parameters.items()
        }
        if set(coefficients) != set(covariates):
            raise ValueError("coefficient_parameters must match covariates exactly")
        if any(not key or not value for key, value in coefficients.items()):
            raise ValueError("effort coefficient parameter names must be non-empty")
        if len(set(coefficients.values())) != len(coefficients):
            raise ValueError("effort coefficient parameter names must be unique")
        object.__setattr__(self, "baseline", baseline)
        object.__setattr__(self, "covariates", covariates)
        object.__setattr__(
            self,
            "coefficient_parameters",
            MappingProxyType(coefficients),
        )

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(self.covariates)

    def priors(self) -> dict[str, PriorSpec]:
        return {
            parameter: PriorSpec("Normal", {"loc": 0.0, "scale": 1.0})
            for parameter in self.coefficient_parameters.values()
        }

    def _linear_predictor(self, key, *, theta, covariates):
        if key not in covariates:
            raise KeyError(f"missing observation-effort covariates for {key!r}")
        value = 0.0
        for covariate in self.covariates:
            parameter = self.coefficient_parameters[covariate]
            if parameter not in theta:
                raise KeyError(
                    f"missing observation-effort parameter {parameter!r}"
                )
            if covariate not in covariates[key]:
                raise KeyError(
                    f"missing observation-effort covariate {covariate!r} for {key!r}"
                )
            value = value + theta[parameter] * covariates[key][covariate]
        return value

    def at(
        self,
        key: tuple[str, int, int],
        *,
        theta,
        covariates,
        exp_fn=math.exp,
    ):
        return self.baseline * exp_fn(
            self._linear_predictor(
                key,
                theta=theta,
                covariates=covariates,
            )
        )

    def array(
        self,
        keys,
        *,
        theta,
        covariates,
        array_module,
    ):
        values = array_module.zeros((len(keys),))
        for covariate in self.covariates:
            parameter = self.coefficient_parameters[covariate]
            if parameter not in theta:
                raise KeyError(
                    f"missing observation-effort parameter {parameter!r}"
                )
            missing = [
                key
                for key in keys
                if key not in covariates or covariate not in covariates[key]
            ]
            if missing:
                raise KeyError(
                    f"missing observation-effort covariate {covariate!r} "
                    f"for {missing[0]!r}"
                )
            x = array_module.asarray(
                [covariates[key][covariate] for key in keys]
            )
            values = values + theta[parameter] * x
        return self.baseline * array_module.exp(values)

    def structural_exposure_mask(self, keys) -> tuple[bool, ...]:
        return tuple(True for _ in keys)
