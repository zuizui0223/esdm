"""Spatial latent-field primitives for FIELD1."""

from .diagnostics import (
    PrecisionSensitivityDiagnostics,
    PrecisionSensitivitySweep,
    edge_axis_correlation,
    precision_sensitivity_diagnostics,
    precision_sensitivity_sweep,
)
from .graph import (
    FrozenSpatialGraph,
    FrozenSpatialProjection,
    ProjectionRow,
    SpatialEdge,
    centered_edge_design_rank,
)
from .precision import (
    dense_precision_array,
    dense_precision_python,
    whitened_field_array,
    whitened_field_python,
    zero_sum_basis_array,
    zero_sum_basis_python,
)

__all__ = [
    "PrecisionSensitivityDiagnostics",
    "PrecisionSensitivitySweep",
    "edge_axis_correlation",
    "precision_sensitivity_diagnostics",
    "precision_sensitivity_sweep",
    "FrozenSpatialGraph",
    "FrozenSpatialProjection",
    "ProjectionRow",
    "SpatialEdge",
    "centered_edge_design_rank",
    "dense_precision_array",
    "dense_precision_python",
    "whitened_field_array",
    "whitened_field_python",
    "zero_sum_basis_array",
    "zero_sum_basis_python",
]
