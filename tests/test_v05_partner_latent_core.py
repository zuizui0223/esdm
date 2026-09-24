import importlib.util
import math

import pytest

from esdm.domain import Grid
from esdm.model import CyclicProcessDependencyError, Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability, PartnerIntensityEffect


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _stream(name, grid, target, informs, effort=1.0):
    return PresenceOnly(
        name,
        effort=EffortField({key: effort for key in grid.keys}),
        informs=frozenset(informs),
        targets=frozenset({target}),
    )


def _directed_model(*, source_effort=1.0):
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    source = (
        LinearSuitability((), "source_intercept", {}),
    )
    focal = (
        LinearSuitability((), "focal_intercept", {}),
        PartnerIntensityEffect(
            source_species="source",
            coefficient_parameter="beta_partner",
            name="partner_effect",
        ),
    )
    model = Model(
        grid,
        {
            "focal": focal,
            "source": source,
        },
        (
            _stream(
                "source_records",
                grid,
                "source",
                {"suitability"},
                effort=source_effort,
            ),
            _stream(
                "focal_records",
                grid,
                "focal",
                {"suitability", "partner_effect"},
            ),
        ),
    )
    theta = {
        "source": {"source_intercept": math.log(2.0)},
        "focal": {
            "focal_intercept": math.log(4.0),
            "beta_partner": 1.0,
        },
    }
    covariates = {key: {} for key in grid.keys}
    return grid, model, theta, covariates


def test_partner_effect_uses_source_latent_field_despite_reverse_declaration_order():
    grid, model, theta, covariates = _directed_model()

    fields = model.latent_fields(theta, covariates)

    assert model._species_topological_order() == ("source", "focal")
    assert all(
        fields.log_intensity["source"][key] == pytest.approx(math.log(2.0))
        for key in grid.keys
    )
    assert all(
        fields.log_intensity["focal"][key] == pytest.approx(math.log(12.0))
        for key in grid.keys
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_partner_effect_scalar_and_array_paths_match():
    import jax.numpy as jnp

    grid, model, theta, covariates = _directed_model()
    scalar = model.latent_fields(theta, covariates)
    array = model.latent_field_arrays(theta, covariates, array_module=jnp)

    assert list(map(float, array.log_intensity["source"].values)) == pytest.approx(
        [scalar.log_intensity["source"][key] for key in grid.keys]
    )
    assert list(map(float, array.log_intensity["focal"].values)) == pytest.approx(
        [scalar.log_intensity["focal"][key] for key in grid.keys]
    )


def test_partner_effect_knockout_removes_only_directed_effect():
    grid, model, _theta, covariates = _directed_model()
    knocked = model.knockout("focal", "partner_effect")

    fields = knocked.latent_fields(
        {
            "source": {"source_intercept": math.log(2.0)},
            "focal": {"focal_intercept": math.log(4.0)},
        },
        covariates,
    )

    assert all(
        fields.log_intensity["focal"][key] == pytest.approx(math.log(4.0))
        for key in grid.keys
    )


def test_partner_effect_uses_latent_ecology_not_source_observation_effort():
    _grid, low, theta, covariates = _directed_model(source_effort=1.0)
    _grid, high, _theta, _covariates = _directed_model(source_effort=100.0)

    low_fields = low.latent_fields(theta, covariates)
    high_fields = high.latent_fields(theta, covariates)

    assert low_fields.log_intensity["focal"] == high_fields.log_intensity["focal"]


def test_unknown_partner_dependency_fails_closed():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    with pytest.raises(ValueError, match="unknown latent species dependency"):
        Model(
            grid,
            {
                "focal": (
                    PartnerIntensityEffect(
                        source_species="missing",
                        coefficient_parameter="beta",
                        name="partner_effect",
                    ),
                )
            },
            (
                _stream(
                    "records",
                    grid,
                    "focal",
                    {"partner_effect"},
                ),
            ),
        )


def test_reciprocal_partner_dependencies_remain_unsupported():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    with pytest.raises(CyclicProcessDependencyError):
        Model(
            grid,
            {
                "a": (
                    PartnerIntensityEffect(
                        source_species="b",
                        coefficient_parameter="beta_b",
                        name="from_b",
                    ),
                ),
                "b": (
                    PartnerIntensityEffect(
                        source_species="a",
                        coefficient_parameter="beta_a",
                        name="from_a",
                    ),
                ),
            },
            (
                _stream("a_records", grid, "a", {"from_b"}),
                _stream("b_records", grid, "b", {"from_a"}),
            ),
        )
