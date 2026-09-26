"""Observation streams and compatibility next-observation primitives."""

from .blocks import PoissonObservationBlock
from .detection import KnownDetection, LogitDetection
from .effort import EffortField, LogLinearEffort, MultiLogLinearEffort
from .presence_only import PresenceOnly
from .state_annotated import StateAnnotatedCount
from .state_composition import StateCompositionCount
from .candidates import (
    DiscriminatingObservationSet,
    ObservationCandidate,
    nominate_discriminating_observations,
)

__all__ = [
    "PoissonObservationBlock",
    "KnownDetection",
    "LogitDetection",
    "EffortField",
    "LogLinearEffort",
    "MultiLogLinearEffort",
    "PresenceOnly",
    "StateAnnotatedCount",
    "StateCompositionCount",
    "DiscriminatingObservationSet",
    "ObservationCandidate",
    "nominate_discriminating_observations",
]
