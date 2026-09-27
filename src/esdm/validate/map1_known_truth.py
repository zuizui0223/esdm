"""Response-free MAP1 known-truth universe.

MAP1 asks whether a fixed geography-only coherence prior improves held-out maps beyond
both an environment-only model and an equally flexible exchangeable residual field.
It does not estimate or interpret covariance mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from types import MappingProxyType

from esdm.domain import Grid
from esdm.field import FrozenSpatialGraph, SpatialEdge
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import (
    ExchangeableMapField,
    FixedCoherenceMapField,
    LinearSuitability,
)


MODEL_IDS = ("B0", "BX", "BC")
WORLD_IDS = ("N0", "N1", "P1")


@dataclass(frozen=True, slots=True)
class Map1Fixture:
    graph: FrozenSpatialGraph
    grid: Grid
    covariates: object
    h1_heldout_spaces: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType(
                {
                    key: MappingProxyType(dict(values))
                    for key, values in dict(self.covariates).items()
                }
            ),
        )

    def heldout_spaces(self) -> tuple[str, ...]:
        return self.h1_heldout_spaces

    def training_spaces(self) -> tuple[str, ...]:
        heldout = set(self.h1_heldout_spaces)
        return tuple(space for space in self.grid.space if space not in heldout)


@dataclass(frozen=True, slots=True)
class Map1World:
    world_id: str
    truth_model_id: str
    expected_positive_comparisons: tuple[tuple[str, str, str], ...]
    expected_null_comparisons: tuple[tuple[str, str, str], ...]

    def __post_init__(self) -> None:
        if self.world_id not in WORLD_IDS:
            raise ValueError("unknown MAP1 world")
        if self.truth_model_id not in MODEL_IDS:
            raise ValueError("unknown MAP1 truth model")


def _name(column: int, row: int) -> str:
    return f"m{column}r{row}"


def make_map1_fixture() -> Map1Fixture:
    """Irregular 5 x 4 graph; edge lengths are normalized before model use."""

    xs = (0.0, 1.0, 2.2, 3.6, 5.1)
    ys = (0.0, 1.1, 2.5, 4.2)
    coordinates = {
        _name(column, row): (xs[column], ys[row])
        for column in range(len(xs))
        for row in range(len(ys))
    }
    raw_edges = []
    for column in range(len(xs)):
        for row in range(len(ys)):
            left = _name(column, row)
            if column + 1 < len(xs):
                right = _name(column + 1, row)
                x0, y0 = coordinates[left]
                x1, y1 = coordinates[right]
                raw_edges.append((left, right, math.hypot(x1 - x0, y1 - y0)))
            if row + 1 < len(ys):
                right = _name(column, row + 1)
                x0, y0 = coordinates[left]
                x1, y1 = coordinates[right]
                raw_edges.append((left, right, math.hypot(x1 - x0, y1 - y0)))

    ordered_lengths = sorted(length for _left, _right, length in raw_edges)
    midpoint = len(ordered_lengths) // 2
    if len(ordered_lengths) % 2:
        reference = ordered_lengths[midpoint]
    else:
        reference = 0.5 * (
            ordered_lengths[midpoint - 1] + ordered_lengths[midpoint]
        )
    edges = tuple(
        SpatialEdge(left, right, distance=length / reference)
        for left, right, length in raw_edges
    )
    nodes = tuple(coordinates)
    graph = FrozenSpatialGraph(nodes=nodes, edges=edges)

    raw_env = {
        node: 0.55 * x - 0.22 * y
        for node, (x, y) in coordinates.items()
    }
    values = tuple(raw_env.values())
    center = math.fsum(values) / len(values)
    sd = math.sqrt(
        math.fsum((value - center) ** 2 for value in values) / len(values)
    )

    grid = Grid(space=nodes, doy=(60, 180, 300), hour=(12,))
    covariates = {}
    for key in grid.keys:
        space, day, _hour = key
        phase = 2.0 * math.pi * float(day) / 365.0
        covariates[key] = {
            "mean_env": (raw_env[space] - center) / sd,
            "season": math.sin(phase),
        }

    return Map1Fixture(
        graph=graph,
        grid=grid,
        covariates=covariates,
        h1_heldout_spaces=(_name(2, 1), _name(2, 2)),
    )


def _field(fixture: Map1Fixture, model_id: str):
    if model_id == "B0":
        return None
    if model_id == "BX":
        return ExchangeableMapField(fixture.graph)
    if model_id == "BC":
        return FixedCoherenceMapField(
            fixture.graph,
            fixed_rho=1.0,
            alpha=0.90,
        )
    raise KeyError(model_id)


def make_map1_model(
    fixture: Map1Fixture,
    model_id: str,
    *,
    domain_spaces=None,
) -> Model:
    model_id = str(model_id).upper()
    if model_id not in MODEL_IDS:
        raise KeyError(model_id)
    spaces = (
        tuple(fixture.grid.space)
        if domain_spaces is None
        else tuple(str(space) for space in domain_spaces)
    )
    if not spaces or len(set(spaces)) != len(spaces):
        raise ValueError("MAP1 domain spaces must be non-empty and unique")
    unknown = set(spaces) - set(fixture.grid.space)
    if unknown:
        raise ValueError(f"unknown MAP1 spaces: {sorted(unknown)!r}")

    domain = Grid(
        space=spaces,
        doy=fixture.grid.doy,
        hour=fixture.grid.hour,
    )
    suitability = LinearSuitability(
        covariates=("mean_env", "season"),
        intercept_parameter="intercept",
        coefficient_parameters={
            "mean_env": "beta_mean_env",
            "season": "beta_season",
        },
    )
    processes = [suitability]
    field = _field(fixture, model_id)
    informs = {"suitability"}
    if field is not None:
        processes.append(field)
        informs.add(field.name)

    stream = PresenceOnly(
        "records",
        effort=EffortField({key: 6.0 for key in domain.keys}),
        detection_probability=1.0,
        informs=frozenset(informs),
        targets=frozenset({"sp"}),
    )
    return Model(domain, {"sp": tuple(processes)}, (stream,))


def map1_truth_theta(
    fixture: Map1Fixture,
    model_id: str,
    *,
    innovation_seed: int | None = None,
):
    model = make_map1_model(fixture, model_id)
    theta = {
        "intercept": 1.15,
        "beta_mean_env": 0.45,
        "beta_season": 0.20,
    }
    if model_id != "B0":
        field = model.species["sp"][1]
        theta[field.sigma_parameter] = 0.55
        if innovation_seed is None:
            innovations = tuple(
                0.55 * math.sin(0.7 + 1.31 * index)
                for index in range(fixture.graph.node_count - 1)
            )
        else:
            rng = random.Random(int(innovation_seed))
            innovations = tuple(
                rng.gauss(0.0, 1.0)
                for _ in range(fixture.graph.node_count - 1)
            )
        for index, value in enumerate(innovations):
            theta[field.innovation_parameter(index)] = value
    expected = {
        parameter
        for process in model.species["sp"]
        for parameter in process.priors()
    }
    if set(theta) != expected:
        raise RuntimeError("MAP1 truth parameter surface drift")
    return {"sp": theta}


def make_map1_worlds() -> tuple[Map1World, ...]:
    return (
        Map1World(
            "N0",
            "B0",
            (),
            (
                ("BC", "B0", "H1"),
                ("BX", "B0", "H1"),
                ("BC", "BX", "H1"),
            ),
        ),
        Map1World(
            "N1",
            "BX",
            (),
            (("BC", "BX", "H1"),),
        ),
        Map1World(
            "P1",
            "BC",
            (
                ("BC", "B0", "H1"),
                ("BC", "BX", "H1"),
            ),
            (),
        ),
    )


def subset_map1_data(data, model: Model):
    allowed = set(model.domain.keys)
    return {
        "records": {
            "sp": {
                key: int(value)
                for key, value in data["records"]["sp"].items()
                if key in allowed
            }
        }
    }
