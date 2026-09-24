"""Canonical claims-layer access to evidence authorization."""

from esdm.authorization import (
    AuthorizedInteractionEvent,
    AuthorizedObservation,
    InteractionEventRecord,
    ObservationRecord,
    authorize_interaction_event,
    authorize_observation,
)

__all__ = [
    "AuthorizedObservation",
    "ObservationRecord",
    "authorize_observation",
    "AuthorizedInteractionEvent",
    "InteractionEventRecord",
    "authorize_interaction_event",
]
