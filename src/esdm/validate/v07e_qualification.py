"""Pre-outcome matched-model qualification for v0.7e."""

from __future__ import annotations

from dataclasses import dataclass

from .v07d_qualification import evaluate_v07d_identification


@dataclass(frozen=True, slots=True)
class V07EQualification:
    dynamic_structural_pass: bool
    dynamic_practical_pass: bool
    static_structural_pass: bool
    static_practical_pass: bool


def evaluate_v07e_identification() -> V07EQualification:
    source = evaluate_v07d_identification()
    return V07EQualification(
        dynamic_structural_pass=source.dynamic_structural_pass,
        dynamic_practical_pass=source.dynamic_practical_pass,
        static_structural_pass=source.static_structural_pass,
        static_practical_pass=source.static_practical_pass,
    )
