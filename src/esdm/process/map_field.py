"""Interpretation-bounded map fields for the independent MAP1 programme."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from esdm.field import (
    FrozenSpatialGraph,
    FrozenSpatialProjection,
    whitened_field_array,
    whitened_field_python,
    zero_sum_basis_array,
    zero_sum_basis_python,
)
from .base import NoEffectProcess, PriorSpec, ProcessContribution


def _validate_positive(name: str, value: float) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return numeric


def _coherent_unit_rms_scale(
    graph: FrozenSpatialGraph,
    *,
    fixed_rho: float,
    alpha: float,
) -> float:
    """Match coherent and exchangeable prior energy for sigma=1.

    For the exchangeable zero-sum field, E[||u||^2] = m-1 when sigma=1.
    The fixed-coherence transform generally changes that total variance.  MAP1 rescales
    the coherent transform by a response-blind constant so sigma has the same RMS
    amplitude meaning in BC and BX; only correlation structure differs.
    """

    dimension = graph.node_count - 1
    if dimension < 1:
        raise ValueError("MAP1 coherent field requires at least two graph nodes")
    total_energy = 0.0
    for column in range(dimension):
        innovations = [0.0 for _ in range(dimension)]
        innovations[column] = 1.0
        values = whitened_field_python(
            graph,
            innovations,
            rho=float(fixed_rho),
            gamma=0.0,
            beta=0.0,
            sigma=1.0,
            alpha=float(alpha),
        )
        total_energy += math.fsum(float(value) * float(value) for value in values)
    if not math.isfinite(total_energy) or total_energy <= 0.0:
        raise ValueError("MAP1 coherent prior energy must be finite and positive")
    return math.sqrt(dimension / total_energy)



@dataclass(frozen=True, slots=True)
class FixedCoherenceMapField:
    """Spatially coherent residual field with response-blind fixed kernel shape.

    MAP1 intentionally does not estimate range, environmental dependence, or barriers.
    The kernel shape is a design regularizer. Only field amplitude and whitened latent
    innovations are inferred.
    """

    graph: FrozenSpatialGraph
    projection: FrozenSpatialProjection | None = None
    fixed_rho: float = 1.0
    alpha: float = 0.90
    sigma_prior_scale: float = 0.75
    sigma_parameter: str = "map_sigma"
    innovation_prefix: str = "map_z"
    name: str = "map_coherence"
    output_channel: str = "log_intensity"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "set_coherent_map_field_to_zero"
    _rms_normalization: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _validate_positive("fixed_rho", self.fixed_rho)
        _validate_positive("sigma_prior_scale", self.sigma_prior_scale)
        alpha = float(self.alpha)
        if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
            raise ValueError("MAP1 alpha must lie strictly between zero and one")
        projection = self.projection
        if projection is None:
            projection = FrozenSpatialProjection.identity(self.graph)
            object.__setattr__(self, "projection", projection)
        projection.validate_graph(self.graph)
        object.__setattr__(
            self,
            "_rms_normalization",
            _coherent_unit_rms_scale(
                self.graph,
                fixed_rho=float(self.fixed_rho),
                alpha=float(self.alpha),
            ),
        )
        for value in (
            self.sigma_parameter,
            self.innovation_prefix,
            self.name,
        ):
            if not str(value).strip():
                raise ValueError("MAP1 parameter/process names must be non-empty")

    @property
    def rms_normalization(self) -> float:
        return float(self._rms_normalization)

    def innovation_parameter(self, index: int) -> str:
        return f"{self.innovation_prefix}_{int(index):04d}"

    def priors(self) -> dict[str, PriorSpec]:
        output = {
            self.sigma_parameter: PriorSpec(
                "HalfNormal", {"scale": float(self.sigma_prior_scale)}
            )
        }
        for index in range(self.graph.node_count - 1):
            output[self.innovation_parameter(index)] = PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        return output

    def node_field(self, theta):
        innovations = tuple(
            theta[self.innovation_parameter(index)]
            for index in range(self.graph.node_count - 1)
        )
        return whitened_field_python(
            self.graph,
            innovations,
            rho=float(self.fixed_rho),
            gamma=0.0,
            beta=0.0,
            sigma=float(theta[self.sigma_parameter]) * self.rms_normalization,
            alpha=float(self.alpha),
        )

    def node_field_array(self, theta, *, array_module):
        innovations = array_module.stack(
            [
                theta[self.innovation_parameter(index)]
                for index in range(self.graph.node_count - 1)
            ]
        )
        return whitened_field_array(
            self.graph,
            innovations,
            rho=array_module.asarray(float(self.fixed_rho)),
            gamma=array_module.asarray(0.0),
            beta=array_module.asarray(0.0),
            sigma=theta[self.sigma_parameter] * self.rms_normalization,
            alpha=float(self.alpha),
            array_module=array_module,
        )

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        values = self.node_field(theta)
        return ProcessContribution(
            self.output_channel,
            self.projection.project_python(ctx.space, values, self.graph),
        )

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        available = set(self.projection.targets)
        missing = sorted({str(key[0]) for key in keys if str(key[0]) not in available})
        if missing:
            raise KeyError(f"MAP1 projection lacks model spaces: {missing!r}")
        field = self.node_field_array(theta, array_module=array_module)
        values = array_module.stack(
            [
                self.projection.project_array(
                    str(key[0]),
                    field,
                    self.graph,
                    array_module=array_module,
                )
                for key in keys
            ]
        )
        return ProcessContribution(self.output_channel, values)

    def knockout(self):
        return NoEffectProcess(name=self.name, output_channel=self.output_channel)


@dataclass(frozen=True, slots=True)
class ExchangeableMapField:
    """Zero-sum exchangeable residual field used as MAP1's flexibility control."""

    graph: FrozenSpatialGraph
    projection: FrozenSpatialProjection | None = None
    sigma_prior_scale: float = 0.75
    sigma_parameter: str = "map_sigma"
    innovation_prefix: str = "map_z"
    name: str = "map_exchangeable"
    output_channel: str = "log_intensity"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "set_exchangeable_map_field_to_zero"

    def __post_init__(self) -> None:
        _validate_positive("sigma_prior_scale", self.sigma_prior_scale)
        projection = self.projection
        if projection is None:
            projection = FrozenSpatialProjection.identity(self.graph)
            object.__setattr__(self, "projection", projection)
        projection.validate_graph(self.graph)

    def innovation_parameter(self, index: int) -> str:
        return f"{self.innovation_prefix}_{int(index):04d}"

    def priors(self) -> dict[str, PriorSpec]:
        output = {
            self.sigma_parameter: PriorSpec(
                "HalfNormal", {"scale": float(self.sigma_prior_scale)}
            )
        }
        for index in range(self.graph.node_count - 1):
            output[self.innovation_parameter(index)] = PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        return output

    def node_field(self, theta):
        basis = zero_sum_basis_python(self.graph.node_count)
        innovations = tuple(
            float(theta[self.innovation_parameter(index)])
            for index in range(self.graph.node_count - 1)
        )
        sigma = float(theta[self.sigma_parameter])
        return tuple(
            sigma
            * math.fsum(
                basis[node][column] * innovations[column]
                for column in range(self.graph.node_count - 1)
            )
            for node in range(self.graph.node_count)
        )

    def node_field_array(self, theta, *, array_module):
        basis = zero_sum_basis_array(
            self.graph.node_count,
            array_module=array_module,
        )
        innovations = array_module.stack(
            [
                theta[self.innovation_parameter(index)]
                for index in range(self.graph.node_count - 1)
            ]
        )
        return theta[self.sigma_parameter] * (basis @ innovations)

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        values = self.node_field(theta)
        return ProcessContribution(
            self.output_channel,
            self.projection.project_python(ctx.space, values, self.graph),
        )

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        available = set(self.projection.targets)
        missing = sorted({str(key[0]) for key in keys if str(key[0]) not in available})
        if missing:
            raise KeyError(f"MAP1 projection lacks model spaces: {missing!r}")
        field = self.node_field_array(theta, array_module=array_module)
        values = array_module.stack(
            [
                self.projection.project_array(
                    str(key[0]),
                    field,
                    self.graph,
                    array_module=array_module,
                )
                for key in keys
            ]
        )
        return ProcessContribution(self.output_channel, values)

    def knockout(self):
        return NoEffectProcess(name=self.name, output_channel=self.output_channel)


def _cholesky_covariance_python(matrix):
    n = len(matrix)
    lower = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            subtotal = math.fsum(
                lower[i][k] * lower[j][k]
                for k in range(j)
            )
            if i == j:
                diagonal = float(matrix[i][i]) - subtotal
                if diagonal <= 0.0:
                    raise ValueError(
                        "adaptive map covariance must be positive definite"
                    )
                lower[i][j] = math.sqrt(diagonal)
            else:
                lower[i][j] = (
                    float(matrix[i][j]) - subtotal
                ) / lower[j][j]
    return tuple(tuple(row) for row in lower)


def _coherent_coefficient_covariance(
    graph: FrozenSpatialGraph,
    *,
    fixed_rho: float,
    alpha: float,
):
    """Return trace-normalized coherent covariance in zero-sum coordinates."""

    dimension = graph.node_count - 1
    basis = zero_sum_basis_python(graph.node_count)
    scale = _coherent_unit_rms_scale(
        graph,
        fixed_rho=float(fixed_rho),
        alpha=float(alpha),
    )
    transform_columns = []
    for active in range(dimension):
        innovations = [
            1.0 if index == active else 0.0
            for index in range(dimension)
        ]
        node_values = whitened_field_python(
            graph,
            innovations,
            rho=float(fixed_rho),
            gamma=0.0,
            beta=0.0,
            sigma=scale,
            alpha=float(alpha),
        )
        coefficients = tuple(
            math.fsum(
                basis[node][coordinate] * node_values[node]
                for node in range(graph.node_count)
            )
            for coordinate in range(dimension)
        )
        transform_columns.append(coefficients)

    covariance = []
    for row in range(dimension):
        covariance.append(
            tuple(
                math.fsum(
                    transform_columns[column][row]
                    * transform_columns[column][col]
                    for column in range(dimension)
                )
                for col in range(dimension)
            )
        )
    trace = math.fsum(covariance[i][i] for i in range(dimension))
    if not math.isclose(
        trace,
        float(dimension),
        rel_tol=1e-10,
        abs_tol=1e-10,
    ):
        raise RuntimeError(
            "trace-normalized coherent covariance energy drift"
        )
    return tuple(covariance)


@dataclass(frozen=True, slots=True)
class AdaptiveCoherenceMapField:
    """One zero-sum field that interpolates exchangeable and fixed-coherent covariance.

    AMAP1 treats the coherence weight purely as predictive regularization. It is not a
    biological mechanism parameter and is never promoted as evidence that geographic
    coherence is "present".
    """

    graph: FrozenSpatialGraph
    projection: FrozenSpatialProjection | None = None
    fixed_rho: float = 1.0
    alpha: float = 0.90
    sigma_prior_scale: float = 0.75
    coherence_prior_alpha: float = 1.0
    coherence_prior_beta: float = 1.0
    sigma_parameter: str = "map_sigma"
    coherence_parameter: str = "map_coherence_weight"
    innovation_prefix: str = "map_z"
    name: str = "map_adaptive"
    output_channel: str = "log_intensity"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "set_adaptive_map_field_to_zero"
    _coherent_covariance: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _validate_positive("fixed_rho", self.fixed_rho)
        _validate_positive("sigma_prior_scale", self.sigma_prior_scale)
        _validate_positive("coherence_prior_alpha", self.coherence_prior_alpha)
        _validate_positive("coherence_prior_beta", self.coherence_prior_beta)
        alpha = float(self.alpha)
        if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
            raise ValueError("AMAP1 alpha must lie strictly between zero and one")
        projection = self.projection
        if projection is None:
            projection = FrozenSpatialProjection.identity(self.graph)
            object.__setattr__(self, "projection", projection)
        projection.validate_graph(self.graph)
        object.__setattr__(
            self,
            "_coherent_covariance",
            _coherent_coefficient_covariance(
                self.graph,
                fixed_rho=float(self.fixed_rho),
                alpha=float(self.alpha),
            ),
        )
        for value in (
            self.sigma_parameter,
            self.coherence_parameter,
            self.innovation_prefix,
            self.name,
        ):
            if not str(value).strip():
                raise ValueError("AMAP1 parameter/process names must be non-empty")

    @property
    def coherent_coefficient_covariance(self):
        return self._coherent_covariance

    def innovation_parameter(self, index: int) -> str:
        return f"{self.innovation_prefix}_{int(index):04d}"

    def priors(self) -> dict[str, PriorSpec]:
        output = {
            self.sigma_parameter: PriorSpec(
                "HalfNormal", {"scale": float(self.sigma_prior_scale)}
            ),
            self.coherence_parameter: PriorSpec(
                "Beta",
                {
                    "alpha": float(self.coherence_prior_alpha),
                    "beta": float(self.coherence_prior_beta),
                },
            ),
        }
        for index in range(self.graph.node_count - 1):
            output[self.innovation_parameter(index)] = PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        return output

    def _coefficient_covariance_python(self, coherence):
        kappa = float(coherence)
        if not math.isfinite(kappa) or not 0.0 <= kappa <= 1.0:
            raise ValueError("AMAP1 coherence weight must lie in [0, 1]")
        dimension = self.graph.node_count - 1
        return tuple(
            tuple(
                (1.0 - kappa) * (1.0 if row == col else 0.0)
                + kappa * self.coherent_coefficient_covariance[row][col]
                for col in range(dimension)
            )
            for row in range(dimension)
        )

    def node_field(self, theta):
        basis = zero_sum_basis_python(self.graph.node_count)
        covariance = self._coefficient_covariance_python(
            theta[self.coherence_parameter]
        )
        lower = _cholesky_covariance_python(covariance)
        innovations = tuple(
            float(theta[self.innovation_parameter(index)])
            for index in range(self.graph.node_count - 1)
        )
        coefficients = tuple(
            float(theta[self.sigma_parameter])
            * math.fsum(
                lower[row][column] * innovations[column]
                for column in range(row + 1)
            )
            for row in range(self.graph.node_count - 1)
        )
        return tuple(
            math.fsum(
                basis[node][column] * coefficients[column]
                for column in range(self.graph.node_count - 1)
            )
            for node in range(self.graph.node_count)
        )

    def node_field_array(self, theta, *, array_module):
        dimension = self.graph.node_count - 1
        basis = zero_sum_basis_array(
            self.graph.node_count,
            array_module=array_module,
        )
        coherent = array_module.asarray(
            self.coherent_coefficient_covariance
        )
        identity = array_module.eye(dimension)
        kappa = theta[self.coherence_parameter]
        covariance = (1.0 - kappa) * identity + kappa * coherent
        lower = array_module.linalg.cholesky(covariance)
        innovations = array_module.stack(
            [
                theta[self.innovation_parameter(index)]
                for index in range(dimension)
            ]
        )
        coefficients = (
            theta[self.sigma_parameter] * (lower @ innovations)
        )
        return basis @ coefficients

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        values = self.node_field(theta)
        return ProcessContribution(
            self.output_channel,
            self.projection.project_python(ctx.space, values, self.graph),
        )

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        available = set(self.projection.targets)
        missing = sorted(
            {str(key[0]) for key in keys if str(key[0]) not in available}
        )
        if missing:
            raise KeyError(f"AMAP1 projection lacks model spaces: {missing!r}")
        field_values = self.node_field_array(
            theta,
            array_module=array_module,
        )
        values = array_module.stack(
            [
                self.projection.project_array(
                    str(key[0]),
                    field_values,
                    self.graph,
                    array_module=array_module,
                )
                for key in keys
            ]
        )
        return ProcessContribution(self.output_channel, values)

    def knockout(self):
        return NoEffectProcess(
            name=self.name,
            output_channel=self.output_channel,
        )
