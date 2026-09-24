"""Pair-specific interaction-event authorization."""

from __future__ import annotations

from dataclasses import dataclass

from .evidence import ObservationRecord, authorize_observation


def _text(value, label):
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be a non-empty string")
    return result


@dataclass(frozen=True, slots=True)
class InteractionEventRecord:
    """One raw observation about a specific directed source->target event."""

    source: str
    target: str
    observation_id: str
    raw_state: str
    negative_gate_passed: bool = False

    def __post_init__(self) -> None:
        source = _text(self.source, "source")
        target = _text(self.target, "target")
        observation_id = _text(self.observation_id, "observation_id")
        if source == target:
            raise ValueError("interaction event source and target must differ")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "observation_id", observation_id)


@dataclass(frozen=True, slots=True)
class AuthorizedInteractionEvent:
    source: str
    target: str
    observation_id: str
    evidence_state: str
    reason: str
    raw_state: str

    @property
    def is_positive(self) -> bool:
        return self.evidence_state == "positive"

    @property
    def is_negative(self) -> bool:
        return self.evidence_state == "negative"


def authorize_interaction_event(
    record: InteractionEventRecord,
) -> AuthorizedInteractionEvent:
    """Authorize one pair-specific event using the generic observation rules."""

    authorized = authorize_observation(
        ObservationRecord(
            observation_id=record.observation_id,
            raw_state=record.raw_state,
            negative_gate_passed=record.negative_gate_passed,
        )
    )
    return AuthorizedInteractionEvent(
        source=record.source,
        target=record.target,
        observation_id=authorized.observation_id,
        evidence_state=authorized.evidence_state,
        reason=authorized.reason,
        raw_state=authorized.raw_state,
    )
