"""Promotion-gate logic for the v0.3 generative kernel.

The gate intentionally separates in-model calibration from process knockout recovery,
sensitivity to deliberate misspecification, and restraint of downstream claims.
Passing one axis cannot compensate for failing another.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
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
