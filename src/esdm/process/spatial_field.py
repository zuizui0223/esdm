"""FIELD1 graph-GMRF contribution to ecological log intensity."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.field import (
    FrozenSpatialGraph,
    FrozenSpatialProjection,
    whitened_field_array,
    whitened_field_python,
)
from .base import NoEffectProcess, PriorSpec, ProcessContribution


@dataclass(frozen=True, slots=True)
class GraphSpatialField:
    """Small-mesh dense graph-GMRF with a whitened iid innovation parameterization."""

    graph: FrozenSpatialGraph
    projection: FrozenSpatialProjection | None = None
    use_environment_dependence: bool = False
    use_barrier_dependence: bool = False
    alpha: float = 0.95
    log_rho_parameter: str = "field_log_rho"
    log_sigma_parameter: str = "field_log_sigma"
    gamma_parameter: str = "field_gamma"
    beta_parameter: str = "field_beta"
    innovation_prefix: str = "field_z"
    name: str = "spatial_field"
    output_channel: str = "log_intensity"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "set_centered_spatial_field_to_zero"

    def __post_init__(self) -> None:
        alpha = float(self.alpha)
        if not 0.0 < alpha < 1.0:
            raise ValueError("FIELD1 alpha must lie strictly between zero and one")

        projection = self.projection
        if projection is None:
            projection = FrozenSpatialProjection.identity(self.graph)
            object.__setattr__(self, "projection", projection)
        projection.validate_graph(self.graph)

        distances = tuple(edge.distance for edge in self.graph.edges)
        if min(distances) == max(distances):
            raise ValueError(
                "FIELD1 rho requires edge-distance variation after graph freezing"
            )
        if self.use_environment_dependence:
            environmental = tuple(
                edge.environmental_dissimilarity
                for edge in self.graph.edges
            )
            if min(environmental) == max(environmental):
                raise ValueError(
                    "FIELD1 gamma requires environmental-dissimilarity variation"
                )
        if self.use_barrier_dependence:
            barriers = tuple(edge.barrier_exposure for edge in self.graph.edges)
            if min(barriers) == max(barriers):
                raise ValueError(
                    "FIELD1 beta requires barrier-exposure variation"
                )

        for value in (
            self.log_rho_parameter,
            self.log_sigma_parameter,
            self.gamma_parameter,
            self.beta_parameter,
            self.innovation_prefix,
            self.name,
        ):
            if not str(value).strip():
                raise ValueError("FIELD1 parameter/process names must be non-empty")

    def innovation_parameter(self, index: int) -> str:
        return f"{self.innovation_prefix}_{int(index):04d}"

    def priors(self) -> dict[str, PriorSpec]:
        output = {
            self.log_rho_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            ),
            self.log_sigma_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            ),
        }
        if self.use_environment_dependence:
            output[self.gamma_parameter] = PriorSpec(
                "HalfNormal", {"scale": 1.0}
            )
        if self.use_barrier_dependence:
            output[self.beta_parameter] = PriorSpec(
                "HalfNormal", {"scale": 1.0}
            )
        for index in range(self.graph.node_count - 1):
            output[self.innovation_parameter(index)] = PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        return output

    def _python_hyperparameters(self, theta):
        rho = math.exp(float(theta[self.log_rho_parameter]))
        sigma = math.exp(float(theta[self.log_sigma_parameter]))
        gamma = (
            float(theta[self.gamma_parameter])
            if self.use_environment_dependence
            else 0.0
        )
        beta = (
            float(theta[self.beta_parameter])
            if self.use_barrier_dependence
            else 0.0
        )
        return rho, gamma, beta, sigma

    def _array_hyperparameters(self, theta, array_module):
        rho = array_module.exp(theta[self.log_rho_parameter])
        sigma = array_module.exp(theta[self.log_sigma_parameter])
        zero = array_module.asarray(0.0)
        gamma = (
            theta[self.gamma_parameter]
            if self.use_environment_dependence
            else zero
        )
        beta = (
            theta[self.beta_parameter]
            if self.use_barrier_dependence
            else zero
        )
        return rho, gamma, beta, sigma

    def node_field(self, theta):
        rho, gamma, beta, sigma = self._python_hyperparameters(theta)
        innovations = tuple(
            theta[self.innovation_parameter(index)]
            for index in range(self.graph.node_count - 1)
        )
        return whitened_field_python(
            self.graph,
            innovations,
            rho=rho,
            gamma=gamma,
            beta=beta,
            sigma=sigma,
            alpha=self.alpha,
        )

    def node_field_array(self, theta, *, array_module):
        rho, gamma, beta, sigma = self._array_hyperparameters(
            theta, array_module
        )
        innovations = array_module.stack(
            [
                theta[self.innovation_parameter(index)]
                for index in range(self.graph.node_count - 1)
            ]
        )
        return whitened_field_array(
            self.graph,
            innovations,
            rho=rho,
            gamma=gamma,
            beta=beta,
            sigma=sigma,
            alpha=self.alpha,
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
        missing = sorted(
            {
                str(key[0])
                for key in keys
                if str(key[0]) not in set(self.projection.targets)
            }
        )
        if missing:
            raise KeyError(
                f"FIELD1 projection lacks model spaces: {missing!r}"
            )
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
        return NoEffectProcess(
            name=self.name,
            output_channel=self.output_channel,
        )
