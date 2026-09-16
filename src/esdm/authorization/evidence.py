"""Observation-process authorization for ecological evidence.

This module deliberately separates a raw field/monitoring record from the
biological evidence state that downstream inference is allowed to consume.
"""

from __future__ import annotations

from dataclasses import dataclass


RAW_STATES = {
    "positive",
    "negative",
    "missing",
    "unresolved",
    "device_failure",
    "occluded",
}
EVIDENCE_STATES = {"positive", "negative", "unavailable"}


def _nonempty_text(value: object, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be a non-empty string")
    return text


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    observation_id: str
    raw_state: str
    negative_gate_passed: bool = False

    def __post_init__(self) -> None:
        observation_id = _nonempty_text(self.observation_id, "observation_id")
        raw_state = _nonempty_text(self.raw_state, "raw_state")
        if raw_state not in RAW_STATES:
            raise ValueError(f"unknown raw_state: {raw_state}")
        if not isinstance(self.negative_gate_passed, bool):
            raise ValueError("negative_gate_passed must be boolean")
        object.__setattr__(self, "observation_id", observation_id)
        object.__setattr__(self, "raw_state", raw_state)


@dataclass(frozen=True, slots=True)
class AuthorizedObservation:
    observation_id: str
    evidence_state: str
    reason: str
    raw_state: str

    def __post_init__(self) -> None:
        if self.evidence_state not in EVIDENCE_STATES:
            raise ValueError(f"unknown evidence_state: {self.evidence_state}")


def authorize_observation(record: ObservationRecord) -> AuthorizedObservation:
    """Convert one raw observation into an authorized evidence state.

    Positive observations are usable as positive evidence. A raw negative becomes
    biological negative evidence only when its explicit negative-evidence gate has
    passed. Missingness/failure/uncertainty and unqualified negatives remain
    ``unavailable`` rather than being coerced to absence.
    """

    if record.raw_state == "positive":
        return AuthorizedObservation(
            record.observation_id,
            "positive",
            "resolved_positive",
            record.raw_state,
        )
    if record.raw_state == "negative":
        if record.negative_gate_passed:
            return AuthorizedObservation(
                record.observation_id,
                "negative",
                "resolved_negative_authorized",
                record.raw_state,
            )
        return AuthorizedObservation(
            record.observation_id,
            "unavailable",
            "negative_not_authorized",
            record.raw_state,
        )
    return AuthorizedObservation(
        record.observation_id,
        "unavailable",
        f"raw_state_{record.raw_state}",
        record.raw_state,
    )
