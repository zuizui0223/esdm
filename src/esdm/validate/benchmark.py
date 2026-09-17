"""Promotion-gate logic for the v0.3 generative kernel.

The gate intentionally separates in-model calibration from process knockout recovery,
sensitivity to deliberate misspecification, and restraint of downstream claims.
Passing one axis cannot compensate for failing another.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping, Sequence
import math


@dataclass(frozen=True, slots=True)
class V03GateThresholds:
    max_sbc_total_variation: float = 0.10
    max_knockout_abs_effect: float = 0.10
    min_wrong_effort_abs_bias: float = 0.20
    min_hidden_driver_abs_bias: float = 0.20

    def __post_init__(self) -> None:
        for name, value in (
            ("max_sbc_total_variation", self.max_sbc_total_variation),
            ("max_knockout_abs_effect", self.max_knockout_abs_effect),
            ("min_wrong_effort_abs_bias", self.min_wrong_effort_abs_bias),
            ("min_hidden_driver_abs_bias", self.min_hidden_driver_abs_bias),
        ):
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
            object.__setattr__(self, name, numeric)


@dataclass(frozen=True, slots=True)
class V03GateEvidence:
    sbc_total_variation: float
    knockout_abs_effect: float
    wrong_effort_abs_bias: float
    hidden_driver_abs_bias: float
    restrained_under_misspecification: bool

    def __post_init__(self) -> None:
        for name in (
            "sbc_total_variation",
            "knockout_abs_effect",
            "wrong_effort_abs_bias",
            "hidden_driver_abs_bias",
        ):
            numeric = float(getattr(self, name))
            if not math.isfinite(numeric) or numeric < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
            object.__setattr__(self, name, numeric)
        if not isinstance(self.restrained_under_misspecification, bool):
            raise ValueError("restrained_under_misspecification must be boolean")


@dataclass(frozen=True, slots=True)
class V03PromotionDecision:
    axes: dict[str, bool]
    promote: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "axes", MappingProxyType(dict(self.axes)))


def _mean(values: Sequence[float], label: str) -> float:
    data = tuple(float(value) for value in values)
    if not data or any(not math.isfinite(value) for value in data):
        raise ValueError(f"{label} must contain finite posterior draws")
    return sum(data) / len(data)


def _draws(mapping: Mapping[str, Sequence[float]], name: str, label: str) -> tuple[float, ...]:
    if name not in mapping:
        raise KeyError(f"{label} missing parameter {name!r}")
    data = tuple(float(value) for value in mapping[name])
    if not data or any(not math.isfinite(value) for value in data):
        raise ValueError(f"{label}.{name} must contain finite posterior draws")
    return data


def reduce_v03_fit_results(
    *,
    sbc_total_variation: float,
    correct_parameter_draws: Mapping[str, Sequence[float]],
    knockout_parameter_draws: Mapping[str, Sequence[float]],
    wrong_effort_parameter_draws: Mapping[str, Sequence[float]],
    hidden_driver_parameter_draws: Mapping[str, Sequence[float]],
    hidden_driver_target: float,
    restrained_under_misspecification: bool | None,
    intercept_parameter: str = "alpha",
    effect_parameter: str = "beta",
) -> V03GateEvidence:
    """Reduce matched posterior fits into promotion-gate evidence.

    Claim restraint is intentionally supplied independently. Posterior bias alone cannot
    certify that the claims layer correctly refused an over-strong interpretation.
    """

    if restrained_under_misspecification is None:
        raise ValueError("claim restraint must be supplied explicitly")
    if not isinstance(restrained_under_misspecification, bool):
        raise ValueError("claim restraint must be boolean")

    correct_alpha = _mean(
        _draws(correct_parameter_draws, intercept_parameter, "correct_parameter_draws"),
        "correct intercept",
    )
    knockout_effect = _draws(
        knockout_parameter_draws, effect_parameter, "knockout_parameter_draws"
    )
    wrong_alpha = _mean(
        _draws(wrong_effort_parameter_draws, intercept_parameter, "wrong_effort_parameter_draws"),
        "wrong-effort intercept",
    )
    hidden_effect = _mean(
        _draws(hidden_driver_parameter_draws, effect_parameter, "hidden_driver_parameter_draws"),
        "hidden-driver effect",
    )
    target = float(hidden_driver_target)
    if not math.isfinite(target):
        raise ValueError("hidden_driver_target must be finite")

    return V03GateEvidence(
        sbc_total_variation=float(sbc_total_variation),
        knockout_abs_effect=sum(abs(value) for value in knockout_effect) / len(knockout_effect),
        wrong_effort_abs_bias=abs(wrong_alpha - correct_alpha),
        hidden_driver_abs_bias=abs(hidden_effect - target),
        restrained_under_misspecification=restrained_under_misspecification,
    )


def evaluate_v03_promotion(
    evidence: V03GateEvidence,
    thresholds: V03GateThresholds | None = None,
) -> V03PromotionDecision:
    thresholds = thresholds or V03GateThresholds()
    axes = {
        "calibration": evidence.sbc_total_variation <= thresholds.max_sbc_total_variation,
        "knockout_recovery": evidence.knockout_abs_effect <= thresholds.max_knockout_abs_effect,
        "misspecification_sensitivity": (
            evidence.wrong_effort_abs_bias >= thresholds.min_wrong_effort_abs_bias
            and evidence.hidden_driver_abs_bias >= thresholds.min_hidden_driver_abs_bias
        ),
        "claim_restraint": evidence.restrained_under_misspecification,
    }
    return V03PromotionDecision(axes=axes, promote=all(axes.values()))
