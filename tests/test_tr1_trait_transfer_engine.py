from __future__ import annotations

import math

from esdm.validate.tr1_trait_transfer import (
    TR1_ENVIRONMENT_COUNT,
    TR1_HELDOUT_TAXA,
    TR1_TAXON_COUNT,
    TR1_TRAINING_TAXA,
    environment_values,
    fit_logistic,
    heldout_taxon_indices,
    seed_for,
    trait_values,
    training_taxon_indices,
)


def test_tr1_geometry_is_fixed_and_taxon_disjoint():
    traits = trait_values()
    environments = environment_values()
    heldout = heldout_taxon_indices()
    training = training_taxon_indices()

    assert len(traits) == TR1_TAXON_COUNT == 30
    assert len(environments) == TR1_ENVIRONMENT_COUNT == 41
    assert len(heldout) == TR1_HELDOUT_TAXA == 10
    assert len(training) == TR1_TRAINING_TAXA == 20
    assert set(heldout).isdisjoint(training)
    assert set(heldout) | set(training) == set(range(30))
    assert heldout == tuple(range(1, 30, 3))
    assert math.isclose(traits[0], -1.45, abs_tol=1e-12)
    assert math.isclose(traits[-1], 1.45, abs_tol=1e-12)
    assert math.isclose(environments[0], -2.0, abs_tol=1e-12)
    assert math.isclose(environments[-1], 2.0, abs_tol=1e-12)


def test_tr1_seed_families_are_deterministic_and_separate():
    assert seed_for("positive", 0) == 20261101
    assert seed_for("positive", 31) == 20261101 + 31 * 97
    assert seed_for("null", 0) == 20262101
    assert seed_for("null", 31) == 20262101 + 31 * 97
    assert seed_for("positive", 4) != seed_for("null", 4)


def test_tr1_logistic_solver_handles_nonseparable_toy_data():
    rows = (
        ((1.0, -1.0), 0),
        ((1.0, -1.0), 1),
        ((1.0, 0.0), 0),
        ((1.0, 0.0), 1),
        ((1.0, 1.0), 0),
        ((1.0, 1.0), 1),
    )
    coefficients, iterations = fit_logistic(rows)

    assert iterations <= 100
    assert len(coefficients) == 2
    assert all(math.isfinite(value) for value in coefficients)
    assert all(abs(value) < 1e-9 for value in coefficients)
