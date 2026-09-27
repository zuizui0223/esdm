import math

import pytest

from esdm.field import (
    edge_axis_correlation,
    precision_sensitivity_diagnostics,
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
