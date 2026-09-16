"""Canonical claims-layer access to set-valued process support.

The implementation remains shared with the Phase-3 compatibility module during the
refactor; new code should import it from ``esdm.claims``.
"""

from esdm.process.support import (
    ProcessRefinement,
    ProcessSupportSet,
    SeparatorEvidence,
    refine_process_support_set,
)

__all__ = [
    "ProcessRefinement",
    "ProcessSupportSet",
    "SeparatorEvidence",
    "refine_process_support_set",
]
