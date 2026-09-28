import math

import pytest

from esdm.field import (
    FrozenSpatialGraph,
    SpatialEdge,
    edge_axis_correlation,
    precision_sensitivity_diagnostics,
    precision_sensitivity_sweep,
)
from esdm.validate.field1_known_truth import make_field1_fixture


def test_edge_axis_correlation_exposes_practical_near_collinearity():
    fixture = make_field1_fixture()

    full = edge_axis_correlation(
        fixture.graph,
        "distance",
        "environment",
    )
    h1 = edge_axis_correlation(
        fixture.graph,
        "distance",
        "environment",
        spaces=fixture.training_spaces("H1"),
    )
    h2 = edge_axis_correlation(
        fixture.graph,
        "distance",
        "environment",
        spaces=fixture.training_spaces("H2"),
    )

    assert full == pytest.approx(-0.9520338803, abs=1e-8)
    assert h1 == pytest.approx(-0.9494452321, abs=1e-8)
    assert h2 == pytest.approx(-0.9493573365, abs=1e-8)


def test_precision_sensitivity_detects_rho_gamma_alignment():
    fixture = make_field1_fixture()
    result = precision_sensitivity_diagnostics(
        fixture.graph,
        log_rho=math.log(1.4),
        gamma=1.2,
        beta=1.4,
    )

    assert result.derivative_norms["log_rho"] > 0.0
    assert result.derivative_norms["gamma"] > 0.0
    assert result.derivative_norms["beta"] > 0.0
    assert result.cosine[("log_rho", "gamma")] == pytest.approx(
        0.8999357779,
        abs=1e-6,
    )
    assert result.cosine[("log_rho", "beta")] == pytest.approx(
        0.4151587422,
        abs=1e-6,
    )




def test_precision_sensitivity_reports_multi_axis_conditioning():
    fixture = make_field1_fixture()
    result = precision_sensitivity_diagnostics(
        fixture.graph,
        log_rho=math.log(1.4),
        gamma=1.2,
        beta=1.4,
    )

    assert result.axes == ("log_rho", "gamma", "beta")
    assert len(result.normalized_gram) == 3
    assert result.normalized_gram[0][0] == pytest.approx(1.0)
    assert result.normalized_gram[0][1] == pytest.approx(
        result.cosine[("log_rho", "gamma")]
    )
    assert result.normalized_gram_eigenvalues == tuple(
        sorted(result.normalized_gram_eigenvalues)
    )
    assert min(result.normalized_gram_eigenvalues) > 0.0
    assert result.normalized_condition_number == pytest.approx(
        4.7082333,
        rel=1e-5,
    )


def test_two_axis_conditioning_matches_pairwise_cosine_geometry():
    fixture = make_field1_fixture()
    result = precision_sensitivity_diagnostics(
        fixture.graph,
        log_rho=math.log(1.4),
        gamma=0.0,
        beta=0.0,
        axes=("log_rho", "gamma"),
    )
    cosine = result.cosine[("log_rho", "gamma")]
    expected = math.sqrt((1.0 + abs(cosine)) / (1.0 - abs(cosine)))
    assert result.normalized_condition_number == pytest.approx(
        expected,
        rel=1e-7,
    )
    assert result.normalized_condition_number > 6.0


def test_precision_sensitivity_uses_forward_difference_at_nonnegative_boundary():
    fixture = make_field1_fixture()
    result = precision_sensitivity_diagnostics(
        fixture.graph,
        log_rho=math.log(1.4),
        gamma=0.0,
        beta=0.0,
        axes=("log_rho", "gamma"),
    )

    assert result.cosine[("log_rho", "gamma")] > 0.95






def test_precision_sensitivity_sweep_reports_worst_predeclared_point():
    fixture = make_field1_fixture()
    sweep = precision_sensitivity_sweep(
        fixture.graph,
        (
            {"log_rho": math.log(1.4), "gamma": 0.0, "beta": 0.0},
            {"log_rho": math.log(1.4), "gamma": 1.2, "beta": 0.0},
            {"log_rho": math.log(1.4), "gamma": 1.2, "beta": 1.4},
        ),
        axes=("log_rho", "gamma"),
    )

    assert len(sweep.diagnostics) == 3
    assert sweep.worst_point_index == 0
    assert sweep.max_condition_number == pytest.approx(
        sweep.diagnostics[0].normalized_condition_number
    )
    assert sweep.max_condition_number > 6.0
    assert sweep.min_gram_eigenvalue == pytest.approx(
        min(
            min(diagnostic.normalized_gram_eigenvalues)
            for diagnostic in sweep.diagnostics
        )
    )


def test_precision_sensitivity_sweep_fails_closed_on_bad_points():
    fixture = make_field1_fixture()

    with pytest.raises(ValueError, match="at least one point"):
        precision_sensitivity_sweep(fixture.graph, ())

    with pytest.raises(ValueError, match="missing keys"):
        precision_sensitivity_sweep(
            fixture.graph,
            ({"log_rho": 0.0, "gamma": 0.0},),
        )

    with pytest.raises(KeyError, match="unknown keys"):
        precision_sensitivity_sweep(
            fixture.graph,
            (
                {
                    "log_rho": 0.0,
                    "gamma": 0.0,
                    "beta": 0.0,
                    "mystery": 1.0,
                },
            ),
        )


def test_exactly_dependent_precision_axes_have_infinite_condition_number():
    graph = FrozenSpatialGraph(
        nodes=("a", "b", "c", "d"),
        edges=(
            SpatialEdge("a", "b", 1.0, environmental_dissimilarity=2.0),
            SpatialEdge("b", "c", 1.5, environmental_dissimilarity=3.0),
            SpatialEdge("c", "d", 2.0, environmental_dissimilarity=4.0),
            SpatialEdge("a", "d", 3.0, environmental_dissimilarity=6.0),
        ),
    )
    result = precision_sensitivity_diagnostics(
        graph,
        log_rho=math.log(1.2),
        gamma=0.4,
        beta=0.0,
        axes=("log_rho", "gamma"),
    )

    assert min(result.normalized_gram_eigenvalues) == pytest.approx(
        0.0,
        abs=1e-10,
    )
    assert math.isinf(result.normalized_condition_number)


def test_spatial_axis_diagnostics_fail_closed_on_undefined_designs():
    fixture = make_field1_fixture()

    with pytest.raises(KeyError):
        edge_axis_correlation(fixture.graph, "distance", "unknown")

    with pytest.raises(ValueError):
        precision_sensitivity_diagnostics(
            fixture.graph,
            log_rho=0.0,
            gamma=0.0,
            beta=0.0,
            axes=(),
        )
