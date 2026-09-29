"""Generative model composition."""

from .arrays import ContextArray, ContextStateArray, LatentFieldArrays
from .compact import (
    StructuralExposureCompaction,
    compact_model_by_structural_exposure,
    structural_exposure_keys,
)
from .compose import (
    CyclicProcessDependencyError,
    DesignReport,
    DesignUninformedError,
    LatentFields,
    MissingTargetDataError,
    Model,
)

__all__ = [
    "StructuralExposureCompaction",
    "compact_model_by_structural_exposure",
    "structural_exposure_keys",
    "ContextArray",
    "ContextStateArray",
    "LatentFieldArrays",
    "CyclicProcessDependencyError",
    "DesignReport",
    "DesignUninformedError",
    "LatentFields",
    "MissingTargetDataError",
    "Model",
]
