"""Observation/evidence authorization primitives."""

from .evidence import AuthorizedObservation, ObservationRecord, authorize_observation
from .interaction_event import (
    AuthorizedInteractionEvent,
    InteractionEventRecord,
    authorize_interaction_event,
)

__all__ = [
    "AuthorizedObservation",
    "ObservationRecord",
    "authorize_observation",
    "AuthorizedInteractionEvent",
    "InteractionEventRecord",
    "authorize_interaction_event",
]
