import importlib.util
import math

import pytest

from esdm.domain import Context, Grid
from esdm.field import (
    FrozenSpatialGraph,
    FrozenSpatialProjection,
    ProjectionRow,
    SpatialEdge,
    dense_precision_python,
)
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import GraphSpatialField, LinearSuitability


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None
NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def _graph():
    return FrozenSpatialGraph(
        nodes=("a", "b", "c", "d"),
        edges=(
            SpatialEdge("a", "b", 1.0, environmental_dissimilarity=0.2),
            SpatialEdge(
                "b",
                "c",
                1.2,
                environmental_dissimilarity=0.8,
                barrier_exposure=1.0,
            ),
            SpatialEdge("c", "d", 1.5, environmental_dissimilarity=0.1),
            SpatialEdge("a", "d", 2.0, environmental_dissimilarity=0.6),
            SpatialEdge("a", "c", 1.8, environmental_dissimilarity=0.4),
        ),
    )


def _theta(process):
    theta = {
        process.log_rho_parameter: math.log(1.5),
        process.log_sigma_parameter: math.log(0.7),
    }
    if process.use_environment_dependence:
        theta[process.gamma_parameter] = 0.2
    if process.use_barrier_dependence:
        theta[process.beta_parameter] = 0.4
    for index, value in enumerate((1.0, -0.5, 0.25)):
        theta[process.innovation_parameter(index)] = value
    return theta


def test_frozen_graph_rejects_isolated_or_duplicate_edges():
    with pytest.raises(ValueError, match="isolated"):
        FrozenSpatialGraph(
            nodes=("a", "b", "c"),
            edges=(SpatialEdge("a", "b", 1.0),),
        )

    with pytest.raises(ValueError, match="duplicate"):
        FrozenSpatialGraph(
            nodes=("a", "b"),
            edges=(
                SpatialEdge("a", "b", 1.0),
                SpatialEdge("b", "a", 1.2),
            ),
        )


def test_dense_precision_is_symmetric_with_positive_diagonal():
    precision = dense_precision_python(
        _graph(),
        rho=1.4,
        gamma=0.7,
        beta=1.1,
        sigma=0.8,
    )
    assert len(precision) == 4
    for i in range(4):
        assert precision[i][i] > 0.0
        for j in range(4):
            assert precision[i][j] == pytest.approx(precision[j][i])


def test_active_dependence_axes_require_edge_level_variation():
    constant_distance = FrozenSpatialGraph(
        nodes=("a", "b", "c"),
        edges=(
            SpatialEdge("a", "b", 1.0, environmental_dissimilarity=0.1),
            SpatialEdge("b", "c", 1.0, environmental_dissimilarity=0.4),
            SpatialEdge("a", "c", 1.0, environmental_dissimilarity=0.8),
        ),
    )
    with pytest.raises(ValueError, match="rho.*variation"):
        GraphSpatialField(constant_distance)

    constant_environment = FrozenSpatialGraph(
        nodes=("a", "b", "c"),
        edges=(
            SpatialEdge("a", "b", 1.0, environmental_dissimilarity=0.4),
            SpatialEdge("b", "c", 1.2, environmental_dissimilarity=0.4),
            SpatialEdge("a", "c", 1.8, environmental_dissimilarity=0.4),
        ),
    )
    with pytest.raises(ValueError, match="gamma.*variation"):
        GraphSpatialField(
            constant_environment,
            use_environment_dependence=True,
        )

    constant_barrier = FrozenSpatialGraph(
        nodes=("a", "b", "c"),
        edges=(
            SpatialEdge("a", "b", 1.0, barrier_exposure=0.0),
            SpatialEdge("b", "c", 1.2, barrier_exposure=0.0),
            SpatialEdge("a", "c", 1.8, barrier_exposure=0.0),
        ),
    )
    with pytest.raises(ValueError, match="beta.*variation"):
        GraphSpatialField(
            constant_barrier,
            use_barrier_dependence=True,
        )


def test_active_dependence_axes_fail_closed_when_centered_design_is_collinear():
    collinear = FrozenSpatialGraph(
        nodes=("a", "b", "c", "d"),
        edges=(
            SpatialEdge("a", "b", 1.0, environmental_dissimilarity=7.0),
            SpatialEdge("b", "c", 2.0, environmental_dissimilarity=9.0),
            SpatialEdge("c", "d", 3.0, environmental_dissimilarity=11.0),
            SpatialEdge("a", "d", 4.0, environmental_dissimilarity=13.0),
        ),
    )
    with pytest.raises(ValueError, match="exactly collinear"):
        GraphSpatialField(
            collinear,
            use_environment_dependence=True,
        )


def test_spatial_field_is_centered_and_repeated_over_time():
    process = GraphSpatialField(
        _graph(),
        use_environment_dependence=True,
        use_barrier_dependence=True,
    )
    theta = _theta(process)
    field = process.node_field(theta)

    assert math.fsum(field) == pytest.approx(0.0, abs=1e-10)
    assert any(abs(value) > 1e-8 for value in field)

    a_early = process.contribution(Context("a", 20, 0), theta, {}).values
    a_late = process.contribution(Context("a", 200, 18), theta, {}).values
    b_early = process.contribution(Context("b", 20, 0), theta, {}).values
    assert a_early == pytest.approx(a_late)
    assert a_early != pytest.approx(b_early)


def test_frozen_projection_interpolates_unobserved_map_location():
    projection = FrozenSpatialProjection(
        (
            ProjectionRow("mid_ab", (("a", 0.25), ("b", 0.75))),
            ProjectionRow("c_exact", (("c", 1.0),)),
        )
    )
    process = GraphSpatialField(_graph(), projection=projection)
    theta = _theta(process)
    node_field = process.node_field(theta)

    mid = process.contribution(Context("mid_ab", 1, 0), theta, {}).values
    exact = process.contribution(Context("c_exact", 1, 0), theta, {}).values

    assert mid == pytest.approx(0.25 * node_field[0] + 0.75 * node_field[1])
    assert exact == pytest.approx(node_field[2])


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_field1_scalar_and_array_projection_paths_match():
    import jax.numpy as jnp

    projection = FrozenSpatialProjection(
        (
            ProjectionRow("p0", (("a", 1.0),)),
            ProjectionRow("p1", (("a", 0.4), ("b", 0.6))),
            ProjectionRow("p2", (("b", 0.2), ("c", 0.8))),
        )
    )
    process = GraphSpatialField(
        _graph(),
        projection=projection,
        use_environment_dependence=True,
        use_barrier_dependence=True,
    )
    theta = _theta(process)
    keys = (("p0", 1, 0), ("p1", 1, 0), ("p2", 1, 0))

    scalar = [
        process.contribution(Context(*key), theta, {}).values
        for key in keys
    ]
    array = process.contribution_array(
        keys,
        theta,
        {},
        array_module=jnp,
    ).values

    assert list(map(float, array)) == pytest.approx(scalar, rel=1e-5, abs=1e-6)


def test_axis_flags_control_only_declared_hyperparameters():
    distance_only = GraphSpatialField(_graph())
    full = GraphSpatialField(
        _graph(),
        use_environment_dependence=True,
        use_barrier_dependence=True,
    )

    distance_priors = distance_only.priors()
    full_priors = full.priors()

    assert distance_only.gamma_parameter not in distance_priors
    assert distance_only.beta_parameter not in distance_priors
    assert full.gamma_parameter in full_priors
    assert full.beta_parameter in full_priors
    assert full_priors[full.gamma_parameter].distribution == "HalfNormal"
    assert full_priors[full.beta_parameter].distribution == "HalfNormal"
    assert sum(name.startswith(full.innovation_prefix) for name in full_priors) == 3


def test_spatial_field_integrates_with_existing_model_and_knockout():
    grid = Grid(space=("a", "b", "c", "d"), doy=(1,), hour=(0,))
    spatial = GraphSpatialField(_graph())
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability(
                    covariates=(),
                    intercept_parameter="intercept",
                    coefficient_parameters={},
                ),
                spatial,
            )
        },
        (
            PresenceOnly(
                "records",
                effort=EffortField({key: 1.0 for key in grid.keys}),
                detection_probability=1.0,
                informs=frozenset({"suitability", "spatial_field"}),
                targets=frozenset({"sp"}),
            ),
        ),
    )
    theta = {"sp": {"intercept": 0.4, **_theta(spatial)}}
    covariates = {key: {} for key in grid.keys}

    model.check_design()
    full = model.latent_fields(theta, covariates)
    knocked = model.knockout("sp", "spatial_field")
    knocked_fields = knocked.latent_fields(
        {"sp": {"intercept": 0.4}},
        covariates,
    )

    differences = [
        full.log_intensity["sp"][key] - knocked_fields.log_intensity["sp"][key]
        for key in grid.keys
    ]
    assert math.fsum(differences) == pytest.approx(0.0, abs=1e-10)
    assert any(abs(value) > 1e-8 for value in differences)
    assert all(
        knocked_fields.log_intensity["sp"][key] == pytest.approx(0.4)
        for key in grid.keys
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_field1_dense_transform_is_end_to_end_differentiable():
    import jax
    import jax.numpy as jnp

    process = GraphSpatialField(
        _graph(),
        use_environment_dependence=True,
        use_barrier_dependence=True,
    )

    def objective(hyper):
        theta = {
            process.log_rho_parameter: hyper[0],
            process.log_sigma_parameter: hyper[1],
            process.gamma_parameter: hyper[2],
            process.beta_parameter: hyper[3],
            process.innovation_parameter(0): 1.0,
            process.innovation_parameter(1): -0.5,
            process.innovation_parameter(2): 0.25,
        }
        values = process.node_field_array(theta, array_module=jnp)
        return jnp.sum(values * values)

    gradient = jax.grad(objective)(jnp.asarray([0.1, -0.2, 0.3, 0.4]))
    assert tuple(gradient.shape) == (4,)
    assert bool(jnp.all(jnp.isfinite(gradient)))
    assert bool(jnp.any(jnp.abs(gradient) > 1e-8))



@pytest.mark.skipif(
    not NUMPYRO_AVAILABLE,
    reason="NumPyro optional backend not installed",
)
def test_field1_uses_existing_numpyro_prior_and_observation_graph():
    import jax.random as random
    import numpyro.handlers as handlers

    from esdm.model.backend_numpyro import make_numpyro_model
    from esdm.simulate import simulate_presence_only

    grid = Grid(space=("a", "b", "c"), doy=(1, 120), hour=(0,))
    spatial = GraphSpatialField(
        _graph(),
        use_environment_dependence=True,
        use_barrier_dependence=True,
    )
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability(
                    covariates=("x",),
                    intercept_parameter="intercept",
                    coefficient_parameters={"x": "beta_x"},
                ),
                spatial,
            )
        },
        (
            PresenceOnly(
                "records",
                effort=EffortField({key: 3.0 for key in grid.keys}),
                detection_probability=1.0,
                informs=frozenset({"suitability", "spatial_field"}),
                targets=frozenset({"sp"}),
            ),
        ),
    )
    covariates = {
        key: {"x": (-0.5, 0.0, 0.5)[grid.space.index(key[0])]}
        for key in grid.keys
    }
    theta = {
        "sp": {
            "intercept": 0.3,
            "beta_x": 0.2,
            **_theta(spatial),
        }
    }
    generated = simulate_presence_only(
        model,
        theta,
        covariates,
        seed=31,
    )
    program = make_numpyro_model(model, generated.counts, covariates)
    trace = handlers.trace(
        handlers.seed(program, random.PRNGKey(7))
    ).get_trace()

    assert "sp.spatial_field.field_log_rho" in trace
    assert "sp.spatial_field.field_log_sigma" in trace
    assert "sp.spatial_field.field_gamma" in trace
    assert "sp.spatial_field.field_beta" in trace
    assert "sp.spatial_field.field_z_0000" in trace
    assert "sp.spatial_field.field_z_0001" in trace
    assert "sp.spatial_field.field_z_0002" in trace
    assert "sp.spatial_field.field_z_0003" not in trace
    assert "obs.records.sp" in trace
