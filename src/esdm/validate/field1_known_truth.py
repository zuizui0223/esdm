"""Small response-free known-truth universe for the FIELD1 programme."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType

from esdm.domain import Grid
from esdm.field import FrozenSpatialGraph, SpatialEdge
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import GraphSpatialField, LinearSuitability


MODEL_IDS = ("M0", "M1", "M2", "M3", "M4")
PRIMARY_WORLD_IDS = ("K0", "K1", "K2", "K3", "K4")


@dataclass(frozen=True, slots=True)
class Field1Fixture:
    graph: FrozenSpatialGraph
    grid: Grid
    covariates: object
    h1_heldout_spaces: tuple[str, ...]
    h2_heldout_spaces: tuple[str, ...]

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

    @property
    def all_spaces(self) -> tuple[str, ...]:
        return tuple(self.grid.space)

    def training_spaces(self, holdout: str) -> tuple[str, ...]:
        heldout = set(self.heldout_spaces(holdout))
        return tuple(space for space in self.grid.space if space not in heldout)

    def heldout_spaces(self, holdout: str) -> tuple[str, ...]:
        name = str(holdout).upper()
        if name == "H1":
            return self.h1_heldout_spaces
        if name == "H2":
            return self.h2_heldout_spaces
        raise KeyError(f"unknown FIELD1 holdout {holdout!r}")


@dataclass(frozen=True, slots=True)
class Field1KnownTruthWorld:
    world_id: str
    truth_model_id: str
    mean_environment_beta: float
    expected_positive_comparisons: tuple[tuple[str, str, str], ...]
    expected_null_comparisons: tuple[tuple[str, str, str], ...]

    def __post_init__(self) -> None:
        if self.truth_model_id not in MODEL_IDS:
            raise ValueError("unknown FIELD1 truth model")
        if not str(self.world_id).strip():
            raise ValueError("FIELD1 world_id must be non-empty")


def _space_name(column: int, row: int) -> str:
    return f"c{column}r{row}"


def make_field1_fixture() -> Field1Fixture:
    """Create a fixed 4 x 3 graph with a vertical barrier between columns 1 and 2."""

    x_values = (0.0, 1.0, 2.0, 3.0)
    y_values = (0.0, 1.2, 2.5)
    nodes = tuple(
        _space_name(column, row)
        for column in range(len(x_values))
        for row in range(len(y_values))
    )
    coordinates = {
        _space_name(column, row): (x_values[column], y_values[row])
        for column in range(len(x_values))
        for row in range(len(y_values))
    }
    environment = {
        node: x + 0.35 * y
        for node, (x, y) in coordinates.items()
    }

    edges = []
    for column in range(len(x_values)):
        for row in range(len(y_values)):
            left = _space_name(column, row)
            if column + 1 < len(x_values):
                right = _space_name(column + 1, row)
                x0, y0 = coordinates[left]
                x1, y1 = coordinates[right]
                edges.append(
                    SpatialEdge(
                        left,
                        right,
                        math.hypot(x1 - x0, y1 - y0),
                        environmental_dissimilarity=abs(
                            environment[left] - environment[right]
                        ),
                        barrier_exposure=1.0 if column == 1 else 0.0,
                    )
                )
            if row + 1 < len(y_values):
                right = _space_name(column, row + 1)
                x0, y0 = coordinates[left]
                x1, y1 = coordinates[right]
                edges.append(
                    SpatialEdge(
                        left,
                        right,
                        math.hypot(x1 - x0, y1 - y0),
                        environmental_dissimilarity=abs(
                            environment[left] - environment[right]
                        ),
                        barrier_exposure=0.0,
                    )
                )

    graph = FrozenSpatialGraph(nodes=nodes, edges=tuple(edges))
    doy = (45, 135, 225, 315)
    grid = Grid(space=nodes, doy=doy, hour=(12,))

    mean_values = tuple(environment[space] for space in nodes)
    mean_center = math.fsum(mean_values) / len(mean_values)
    mean_sd = math.sqrt(
        math.fsum((value - mean_center) ** 2 for value in mean_values)
        / len(mean_values)
    )
    covariates = {}
    for key in grid.keys:
        space, day, _hour = key
        phase = 2.0 * math.pi * float(day) / 365.0
        covariates[key] = {
            "mean_env": (environment[space] - mean_center) / mean_sd,
            "season": math.sin(phase),
        }

    h1 = tuple(_space_name(column, 2) for column in range(4))
    h2 = tuple(
        _space_name(column, row)
        for column in (2, 3)
        for row in range(3)
    )
    return Field1Fixture(
        graph=graph,
        grid=grid,
        covariates=covariates,
        h1_heldout_spaces=h1,
        h2_heldout_spaces=h2,
    )


def _field_for_model(fixture: Field1Fixture, model_id: str):
    if model_id == "M0":
        return None
    if model_id not in MODEL_IDS:
        raise KeyError(model_id)
    return GraphSpatialField(
        fixture.graph,
        use_environment_dependence=model_id in {"M2", "M4"},
        use_barrier_dependence=model_id in {"M3", "M4"},
    )


def make_field1_model(
    fixture: Field1Fixture,
    model_id: str,
    *,
    domain_spaces=None,
) -> Model:
    """Build one FIELD1 model on a train or held-out domain view.

    The graph and its latent parameterization remain identical across views. Only the
    observation/prediction domain changes, so posterior samples from a training view can
    be evaluated on H1/H2 without zero-effort contexts diluting held-out scores.
    """

    model_id = str(model_id).upper()
    if model_id not in MODEL_IDS:
        raise KeyError(model_id)
    spaces = (
        tuple(fixture.grid.space)
        if domain_spaces is None
        else tuple(str(space) for space in domain_spaces)
    )
    if not spaces or len(set(spaces)) != len(spaces):
        raise ValueError("FIELD1 domain_spaces must be non-empty and unique")
    unknown = set(spaces) - set(fixture.grid.space)
    if unknown:
        raise ValueError(f"unknown FIELD1 domain spaces: {sorted(unknown)}")
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
    field = _field_for_model(fixture, model_id)
    if field is not None:
        processes.append(field)

    effort = EffortField({key: 8.0 for key in domain.keys})
    informs = {"suitability"}
    if field is not None:
        informs.add("spatial_field")
    stream = PresenceOnly(
        "records",
        effort=effort,
        detection_probability=1.0,
        informs=frozenset(informs),
        targets=frozenset({"sp"}),
    )
    return Model(
        domain,
        {"sp": tuple(processes)},
        (stream,),
    )


def field1_truth_theta(
    fixture: Field1Fixture,
    model_id: str,
    *,
    mean_environment_beta: float = 0.55,
):
    model_id = str(model_id).upper()
    model = make_field1_model(fixture, model_id)
    theta = {
        "intercept": 1.35,
        "beta_mean_env": float(mean_environment_beta),
        "beta_season": 0.25,
    }
    if model_id != "M0":
        field = next(
            process
            for process in model.species["sp"]
            if process.name == "spatial_field"
        )
        theta[field.log_rho_parameter] = math.log(1.4)
        theta[field.log_sigma_parameter] = math.log(0.45)
        if field.use_environment_dependence:
            theta[field.gamma_parameter] = 1.2
        if field.use_barrier_dependence:
            theta[field.beta_parameter] = 1.4
        for index in range(fixture.graph.node_count - 1):
            theta[field.innovation_parameter(index)] = (
                0.65 * math.sin(0.9 + 1.7 * index)
            )
    return {"sp": theta}


def make_field1_primary_worlds() -> tuple[Field1KnownTruthWorld, ...]:
    return (
        Field1KnownTruthWorld(
            "K0",
            "M0",
            0.55,
            (),
            (
                ("M1", "M0", "H1"),
                ("M2", "M1", "H1"),
                ("M3", "M1", "H2"),
                ("M4", "M2", "H2"),
            ),
        ),
        Field1KnownTruthWorld(
            "K1",
            "M1",
            0.55,
            (("M1", "M0", "H1"),),
            (
                ("M2", "M1", "H1"),
                ("M3", "M1", "H2"),
                ("M4", "M1", "H2"),
            ),
        ),
        Field1KnownTruthWorld(
            "K2",
            "M2",
            0.55,
            (
                ("M1", "M0", "H1"),
                ("M2", "M1", "H1"),
            ),
            (
                ("M3", "M1", "H2"),
                ("M4", "M2", "H2"),
            ),
        ),
        Field1KnownTruthWorld(
            "K3",
            "M3",
            0.55,
            (
                ("M1", "M0", "H1"),
                ("M3", "M1", "H2"),
            ),
            (
                ("M2", "M1", "H1"),
                ("M4", "M3", "H1"),
            ),
        ),
        Field1KnownTruthWorld(
            "K4",
            "M4",
            0.55,
            (
                ("M1", "M0", "H1"),
                ("M2", "M1", "H1"),
                ("M3", "M1", "H2"),
                ("M4", "M2", "H2"),
                ("M4", "M3", "H1"),
            ),
            (),
        ),
    )


def make_field1_mean_covariance_factorial() -> tuple[Field1KnownTruthWorld, ...]:
    """K5: environmental mean absent/present x covariance absent/present."""

    worlds = []
    for mean_present in (False, True):
        for covariance_present in (False, True):
            world_id = (
                f"K5_mean{int(mean_present)}_cov{int(covariance_present)}"
            )
            worlds.append(
                Field1KnownTruthWorld(
                    world_id=world_id,
                    truth_model_id="M2" if covariance_present else "M1",
                    mean_environment_beta=0.55 if mean_present else 0.0,
                    expected_positive_comparisons=(
                        (("M2", "M1", "H1"),)
                        if covariance_present
                        else ()
                    ),
                    expected_null_comparisons=(
                        ()
                        if covariance_present
                        else (("M2", "M1", "H1"),)
                    ),
                )
            )
    return tuple(worlds)


def matched_barrier_distance_strata(
    fixture: Field1Fixture,
    *,
    decimal_places: int = 8,
):
    """K6 design audit: distances containing barrier and non-barrier edges."""

    grouped = {}
    for edge in fixture.graph.edges:
        distance = round(float(edge.distance), int(decimal_places))
        grouped.setdefault(distance, {0: 0, 1: 0})
        group = 1 if edge.barrier_exposure > 0.0 else 0
        grouped[distance][group] += 1
    return MappingProxyType(
        {
            distance: MappingProxyType(dict(counts))
            for distance, counts in grouped.items()
            if counts[0] > 0 and counts[1] > 0
        }
    )


def subset_presence_data(data, model: Model):
    """Restrict generated records to an explicit train/held-out model domain."""

    allowed = set(model.domain.keys)
    counts = data["records"]["sp"]
    return {
        "records": {
            "sp": {
                key: int(value)
                for key, value in counts.items()
                if key in allowed
            }
        }
    }
