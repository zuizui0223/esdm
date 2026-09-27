"""Frozen response-blind spatial graph declarations for FIELD1."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class SpatialEdge:
    """One undirected FIELD1 graph edge with frozen dependence covariates."""

    left: str
    right: str
    distance: float
    environmental_dissimilarity: float = 0.0
    barrier_exposure: float = 0.0

    def __post_init__(self) -> None:
        left = str(self.left).strip()
        right = str(self.right).strip()
        if not left or not right:
            raise ValueError("edge endpoints must be non-empty")
        if left == right:
            raise ValueError("spatial graph does not allow self edges")
        distance = float(self.distance)
        environmental = float(self.environmental_dissimilarity)
        barrier = float(self.barrier_exposure)
        if distance <= 0.0:
            raise ValueError("edge distance must be positive")
        if environmental < 0.0:
            raise ValueError("environmental dissimilarity must be non-negative")
        if barrier < 0.0 or barrier > 1.0:
            raise ValueError("barrier exposure must lie in [0, 1]")
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "right", right)
        object.__setattr__(self, "distance", distance)
        object.__setattr__(self, "environmental_dissimilarity", environmental)
        object.__setattr__(self, "barrier_exposure", barrier)


@dataclass(frozen=True, slots=True)
class FrozenSpatialGraph:
    """Response-blind graph shared by every FIELD1 knockout model."""

    nodes: tuple[str, ...]
    edges: tuple[SpatialEdge, ...]
    _node_index: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        nodes = tuple(str(value).strip() for value in self.nodes)
        if not nodes or any(not value for value in nodes):
            raise ValueError("graph nodes must be non-empty")
        if len(set(nodes)) != len(nodes):
            raise ValueError("graph nodes must be unique")
        index = {node: i for i, node in enumerate(nodes)}

        edges = tuple(self.edges)
        seen: set[tuple[str, str]] = set()
        degree = {node: 0 for node in nodes}
        for edge in edges:
            if edge.left not in index or edge.right not in index:
                raise ValueError("edge endpoint is absent from graph nodes")
            pair = tuple(sorted((edge.left, edge.right)))
            if pair in seen:
                raise ValueError(f"duplicate undirected edge: {pair!r}")
            seen.add(pair)
            degree[edge.left] += 1
            degree[edge.right] += 1

        isolated = [node for node, value in degree.items() if value == 0]
        if isolated:
            raise ValueError(
                f"FIELD1 graph does not allow isolated nodes: {isolated!r}"
            )

        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "_node_index", MappingProxyType(index))

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def node_index(self):
        return self._node_index

    def edge_indices(self):
        return tuple(
            (self._node_index[edge.left], self._node_index[edge.right], edge)
            for edge in self.edges
        )


@dataclass(frozen=True, slots=True)
class ProjectionRow:
    """One response-blind interpolation row A(s) over FIELD1 graph nodes."""

    target: str
    weights: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        target = str(self.target).strip()
        if not target:
            raise ValueError("projection target must be non-empty")
        cleaned = tuple(
            (str(node).strip(), float(weight))
            for node, weight in self.weights
        )
        if not cleaned:
            raise ValueError("projection row must contain at least one node")
        nodes = [node for node, _weight in cleaned]
        if any(not node for node in nodes) or len(set(nodes)) != len(nodes):
            raise ValueError("projection nodes must be unique non-empty names")
        if any(
            not math.isfinite(weight) or weight < 0.0
            for _node, weight in cleaned
        ):
            raise ValueError("projection weights must be finite and non-negative")
        total = math.fsum(weight for _node, weight in cleaned)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("projection weights must sum to one")
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "weights", cleaned)


@dataclass(frozen=True, slots=True)
class FrozenSpatialProjection:
    """Frozen interpolation operator from graph nodes to named map locations."""

    rows: tuple[ProjectionRow, ...]
    _by_target: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        rows = tuple(self.rows)
        if not rows:
            raise ValueError("FIELD1 projection must contain at least one target")
        targets = [row.target for row in rows]
        if len(set(targets)) != len(targets):
            raise ValueError("FIELD1 projection targets must be unique")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self,
            "_by_target",
            MappingProxyType({row.target: row for row in rows}),
        )

    @classmethod
    def identity(cls, graph: FrozenSpatialGraph) -> "FrozenSpatialProjection":
        return cls(
            tuple(
                ProjectionRow(node, ((node, 1.0),))
                for node in graph.nodes
            )
        )

    @property
    def targets(self) -> tuple[str, ...]:
        return tuple(row.target for row in self.rows)

    def validate_graph(self, graph: FrozenSpatialGraph) -> None:
        unknown = sorted(
            {
                node
                for row in self.rows
                for node, _weight in row.weights
                if node not in graph.node_index
            }
        )
        if unknown:
            raise ValueError(
                f"FIELD1 projection references unknown graph nodes: {unknown!r}"
            )

    def project_python(self, target: str, node_values, graph: FrozenSpatialGraph):
        name = str(target)
        if name not in self._by_target:
            raise KeyError(f"FIELD1 projection has no target {name!r}")
        row = self._by_target[name]
        return math.fsum(
            weight * node_values[graph.node_index[node]]
            for node, weight in row.weights
        )

    def project_array(
        self,
        target: str,
        node_values,
        graph: FrozenSpatialGraph,
        *,
        array_module,
    ):
        name = str(target)
        if name not in self._by_target:
            raise KeyError(f"FIELD1 projection has no target {name!r}")
        row = self._by_target[name]
        return array_module.sum(
            array_module.stack(
                [
                    weight * node_values[graph.node_index[node]]
                    for node, weight in row.weights
                ]
            )
        )
