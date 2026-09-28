"""Response-free AMAP1 multi-geometry known-truth universe."""

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
    AdaptiveCoherenceMapField,
    ExchangeableMapField,
    FixedCoherenceMapField,
    LinearSuitability,
)


MODEL_IDS = ("B0", "BX", "BC", "BA")
GEOMETRY_IDS = ("G1", "G2", "G3")
TRUTH_IDS = ("T0", "TX", "TC")


@dataclass(frozen=True, slots=True)
class AMap1Fixture:
    geometry_id: str
    graph: FrozenSpatialGraph
    grid: Grid
    covariates: object
    heldout_spaces: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.geometry_id not in GEOMETRY_IDS:
            raise ValueError("unknown AMAP1 geometry")
        heldout = tuple(str(space) for space in self.heldout_spaces)
        if not heldout or len(set(heldout)) != len(heldout):
            raise ValueError("AMAP1 heldout spaces must be non-empty and unique")
        unknown = set(heldout) - set(self.grid.space)
        if unknown:
            raise ValueError(f"unknown AMAP1 heldout spaces: {sorted(unknown)!r}")
        if set(heldout) == set(self.grid.space):
            raise ValueError("AMAP1 holdout cannot consume the full geometry")
        object.__setattr__(self, "heldout_spaces", heldout)
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

    @property
    def training_spaces(self) -> tuple[str, ...]:
        heldout = set(self.heldout_spaces)
        return tuple(space for space in self.grid.space if space not in heldout)


@dataclass(frozen=True, slots=True)
class AMap1World:
    world_id: str
    geometry_id: str
    truth_id: str
    truth_model_id: str
    oracle_model_id: str
    detectability_reference: tuple[str, str] | None

    def __post_init__(self) -> None:
        if self.geometry_id not in GEOMETRY_IDS:
            raise ValueError("unknown AMAP1 geometry")
        if self.truth_id not in TRUTH_IDS:
            raise ValueError("unknown AMAP1 truth class")
        if self.truth_model_id not in {"B0", "BX", "BC"}:
            raise ValueError("unknown AMAP1 truth model")
        if self.oracle_model_id != self.truth_model_id:
            raise ValueError("AMAP1 oracle must be fixed by generating truth")


def _normalized_graph(coordinates, raw_pairs):
    lengths = []
    for left, right in raw_pairs:
        x0, y0 = coordinates[left]
        x1, y1 = coordinates[right]
        lengths.append((left, right, math.hypot(x1 - x0, y1 - y0)))
    ordered = sorted(length for _left, _right, length in lengths)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        reference = ordered[midpoint]
    else:
        reference = 0.5 * (ordered[midpoint - 1] + ordered[midpoint])
    if reference <= 0.0:
        raise ValueError("AMAP1 reference edge length must be positive")
    return FrozenSpatialGraph(
        nodes=tuple(coordinates),
        edges=tuple(
            SpatialEdge(left, right, distance=length / reference)
            for left, right, length in lengths
        ),
    )


def _covariates(coordinates, grid):
    raw = {
        node: (
            math.sin(0.71 * x)
            + 0.55 * math.cos(0.93 * y)
            + 0.12 * math.sin(0.31 * x * y)
        )
        for node, (x, y) in coordinates.items()
    }
    values = tuple(raw.values())
    center = math.fsum(values) / len(values)
    sd = math.sqrt(
        math.fsum((value - center) ** 2 for value in values) / len(values)
    )
    if sd <= 0.0:
        raise ValueError("AMAP1 mean environment must vary")
    return {
        key: {
            "mean_env": (raw[key[0]] - center) / sd,
            "season": math.sin(2.0 * math.pi * float(key[1]) / 365.0),
        }
        for key in grid.keys
    }


def _fixture_g1():
    xs = (0.0, 0.9, 2.0, 3.35, 4.85, 6.45)
    ys = (0.0, 1.05, 2.35, 3.95)
    coordinates = {
        f"g1c{column}r{row}": (xs[column], ys[row])
        for column in range(len(xs))
        for row in range(len(ys))
    }
    pairs = []
    for column in range(len(xs)):
        for row in range(len(ys)):
            node = f"g1c{column}r{row}"
            if column + 1 < len(xs):
                pairs.append((node, f"g1c{column + 1}r{row}"))
            if row + 1 < len(ys):
                pairs.append((node, f"g1c{column}r{row + 1}"))
    graph = _normalized_graph(coordinates, pairs)
    grid = Grid(space=tuple(coordinates), doy=(50, 170, 290), hour=(12,))
    heldout = (
        "g1c2r1",
        "g1c2r2",
        "g1c3r1",
        "g1c3r2",
    )
    return AMap1Fixture(
        "G1",
        graph,
        grid,
        _covariates(coordinates, grid),
        heldout,
    )


def _fixture_g2():
    xs = (
        0.0, 0.8, 1.75, 2.9, 4.1, 5.45, 6.6, 7.95,
        9.2, 10.45, 11.8, 13.0, 14.4, 15.65, 17.0, 18.5,
    )
    coordinates = {
        f"g2m{index}": (x, 0.0)
        for index, x in enumerate(xs)
    }
    pairs = [
        (f"g2m{index}", f"g2m{index + 1}")
        for index in range(len(xs) - 1)
    ]
    for base, y in ((3, 1.2), (6, -1.0), (10, 1.35), (13, -1.15)):
        branch = f"g2b{base}"
        coordinates[branch] = (xs[base] + 0.18, y)
        pairs.append((f"g2m{base}", branch))
    graph = _normalized_graph(coordinates, pairs)
    grid = Grid(space=tuple(coordinates), doy=(70, 190, 310), hour=(12,))
    heldout = ("g2m7", "g2m8", "g2m9")
    return AMap1Fixture(
        "G2",
        graph,
        grid,
        _covariates(coordinates, grid),
        heldout,
    )


def _fixture_g3():
    coordinates = {}
    pairs = []
    left_x = (0.0, 0.9, 1.9)
    right_x = (7.0, 8.05, 9.2)
    ys = (0.0, 1.15, 2.45)
    for prefix, xs in (("L", left_x), ("R", right_x)):
        for column in range(3):
            for row in range(3):
                node = f"g3{prefix}c{column}r{row}"
                coordinates[node] = (xs[column], ys[row])
                if column > 0:
                    pairs.append(
                        (f"g3{prefix}c{column - 1}r{row}", node)
                    )
                if row > 0:
                    pairs.append(
                        (f"g3{prefix}c{column}r{row - 1}", node)
                    )
    pairs.extend(
        (
            ("g3Lc2r0", "g3Rc0r0"),
            ("g3Lc2r2", "g3Rc0r2"),
        )
    )
    graph = _normalized_graph(coordinates, pairs)
    grid = Grid(space=tuple(coordinates), doy=(40, 160, 280), hour=(12,))
    heldout = (
        "g3Rc1r1",
        "g3Rc2r1",
        "g3Rc1r2",
    )
    return AMap1Fixture(
        "G3",
        graph,
        grid,
        _covariates(coordinates, grid),
        heldout,
    )


def make_amap1_fixtures():
    fixtures = (_fixture_g1(), _fixture_g2(), _fixture_g3())
    if tuple(fixture.geometry_id for fixture in fixtures) != GEOMETRY_IDS:
        raise RuntimeError("AMAP1 geometry order drift")
    return fixtures


def _field(fixture: AMap1Fixture, model_id: str):
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
    if model_id == "BA":
        return AdaptiveCoherenceMapField(
            fixture.graph,
            fixed_rho=1.0,
            alpha=0.90,
        )
    raise KeyError(model_id)


def make_amap1_model(
    fixture: AMap1Fixture,
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
        raise ValueError("AMAP1 domain spaces must be non-empty and unique")
    unknown = set(spaces) - set(fixture.grid.space)
    if unknown:
        raise ValueError(f"unknown AMAP1 spaces: {sorted(unknown)!r}")

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


def amap1_truth_theta(
    fixture: AMap1Fixture,
    truth_model_id: str,
    *,
    innovation_seed: int,
):
    model_id = str(truth_model_id).upper()
    if model_id not in {"B0", "BX", "BC"}:
        raise ValueError("AMAP1 truth must be B0, BX, or BC")
    model = make_amap1_model(fixture, model_id)
    theta = {
        "intercept": 1.10,
        "beta_mean_env": 0.42,
        "beta_season": 0.18,
    }
    if model_id != "B0":
        field = model.species["sp"][1]
        theta[field.sigma_parameter] = 0.55
        rng = random.Random(int(innovation_seed))
        for index in range(fixture.graph.node_count - 1):
            theta[field.innovation_parameter(index)] = rng.gauss(0.0, 1.0)
    expected = {
        parameter
        for process in model.species["sp"]
        for parameter in process.priors()
    }
    if set(theta) != expected:
        raise RuntimeError("AMAP1 truth parameter surface drift")
    return {"sp": theta}


def make_amap1_worlds():
    truth_to_model = {"T0": "B0", "TX": "BX", "TC": "BC"}
    detectability = {
        "T0": None,
        "TX": ("BX", "B0"),
        "TC": ("BC", "B0"),
    }
    worlds = []
    for fixture in make_amap1_fixtures():
        for truth_id in TRUTH_IDS:
            model_id = truth_to_model[truth_id]
            worlds.append(
                AMap1World(
                    world_id=f"{fixture.geometry_id}_{truth_id}",
                    geometry_id=fixture.geometry_id,
                    truth_id=truth_id,
                    truth_model_id=model_id,
                    oracle_model_id=model_id,
                    detectability_reference=detectability[truth_id],
                )
            )
    return tuple(worlds)


def subset_amap1_data(data, model: Model):
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
