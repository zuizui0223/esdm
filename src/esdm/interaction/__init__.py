"""Generic state-resolved biotic-interaction primitives."""

from .biotic_gain import biotic_information_gain
from .opportunity import interaction_opportunity
from .overlap import geographic_overlap, overlap_coefficient, state_overlap

__all__ = [
    "biotic_information_gain",
    "geographic_overlap",
    "interaction_opportunity",
    "overlap_coefficient",
    "state_overlap",
]
