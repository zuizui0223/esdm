"""Deterministic non-skippable information-transfer ceiling."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class TransferStepResult:
    step: str
    next_level: str
    status: str
    minimum_gain: float | None


@dataclass(frozen=True, slots=True)
class PointTransferCeiling:
    base_level: str
    level: str
    tolerance: float
    steps: tuple[TransferStepResult, ...]


def point_transfer_ceiling(
    *,
    base_level: str,
    ordered_steps: Sequence[tuple[str, str]],
    gains_by_step: Mapping[str, Sequence[float]],
    tolerance: float = 0.0,
) -> PointTransferCeiling:
    """Advance only through consecutive all-group positive transfer steps.

    This is a point diagnostic. It does not provide a confidence guarantee.
    """

    if not isinstance(base_level, str) or not base_level.strip():
        raise ValueError("base_level must be a non-empty string")
    tolerance = float(tolerance)
    if not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite")

    names = [step for step, _ in ordered_steps]
    if len(set(names)) != len(names):
        raise ValueError("transfer step names must be unique")

    current_level = base_level
    stopped = False
    results: list[TransferStepResult] = []

    for step, next_level in ordered_steps:
        if not isinstance(step, str) or not step.strip():
            raise ValueError("step names must be non-empty strings")
        if not isinstance(next_level, str) or not next_level.strip():
            raise ValueError("next levels must be non-empty strings")

        if stopped:
            results.append(
                TransferStepResult(
                    step=step,
                    next_level=next_level,
                    status="not_reached",
                    minimum_gain=None,
                )
            )
            continue

        gains = gains_by_step.get(step)
        if gains is None or len(gains) == 0:
            results.append(
                TransferStepResult(step, next_level, "unavailable", None)
            )
            stopped = True
            continue

        gain_values = [float(value) for value in gains]
        if any(not math.isfinite(value) for value in gain_values):
            results.append(
                TransferStepResult(step, next_level, "unavailable", None)
            )
            stopped = True
            continue

        minimum_gain = min(gain_values)
        if all(value > tolerance for value in gain_values):
            current_level = next_level
            results.append(
                TransferStepResult(step, next_level, "pass", minimum_gain)
            )
        else:
            results.append(
                TransferStepResult(step, next_level, "fail", minimum_gain)
            )
            stopped = True

    return PointTransferCeiling(
        base_level=base_level,
        level=current_level,
        tolerance=tolerance,
        steps=tuple(results),
    )
