import math

import pytest

from esdm.validate.amap1_known_truth import (
    GEOMETRY_IDS,
    MODEL_IDS,
    TRUTH_IDS,
    amap1_truth_theta,
    make_amap1_fixtures,
    make_amap1_model,
    make_amap1_worlds,
)


def _median(values):
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def test_amap1_geometry_family_is_finite_and_response_blind():
    fixtures = make_amap1_fixtures()

    assert tuple(fixture.geometry_id for fixture in fixtures) == GEOMETRY_IDS
    assert len(fixtures) == 3

    for fixture in fixtures:
        assert fixture.training_spaces
        assert fixture.heldout_spaces
        assert set(fixture.training_spaces).isdisjoint(fixture.heldout_spaces)
        assert (
            set(fixture.training_spaces) | set(fixture.heldout_spaces)
            == set(fixture.grid.space)
        )
        assert _median(edge.distance for edge in fixture.graph.edges) == pytest.approx(
            1.0,
            rel=1e-12,
            abs=1e-12,
        )
        assert set(fixture.covariates) == set(fixture.grid.keys)
        for values in fixture.covariates.values():
            assert set(values) == {"mean_env", "season"}


def test_amap1_geometry_holdouts_match_declared_shapes():
    fixtures = {
        fixture.geometry_id: fixture
        for fixture in make_amap1_fixtures()
    }

    assert len(fixtures["G1"].heldout_spaces) == 4
    assert set(fixtures["G1"].heldout_spaces) == {
        "g1c2r1",
        "g1c2r2",
        "g1c3r1",
        "g1c3r2",
    }

    assert fixtures["G2"].heldout_spaces == (
        "g2m7",
        "g2m8",
        "g2m9",
    )
    assert "g2m6" in fixtures["G2"].training_spaces
    assert "g2m10" in fixtures["G2"].training_spaces

    assert all(
        space.startswith("g3R")
        for space in fixtures["G3"].heldout_spaces
    )
    bridge_pairs = {
        frozenset((edge.left, edge.right))
        for edge in fixtures["G3"].graph.edges
        if {edge.left[2:3], edge.right[2:3]} == {"L", "R"}
    }
    assert len(bridge_pairs) == 2


def test_amap1_model_family_is_design_informed_on_every_geometry():
    for fixture in make_amap1_fixtures():
        for model_id in MODEL_IDS:
            model = make_amap1_model(fixture, model_id)
            report = model.check_design()
            assert ("sp", "suitability") in report.informed_processes
            if model_id == "B0":
                assert len(report.informed_processes) == 1
            else:
                assert len(report.informed_processes) == 2


def test_amap1_worlds_cross_every_geometry_and_truth_class_once():
    worlds = make_amap1_worlds()
    assert len(worlds) == len(GEOMETRY_IDS) * len(TRUTH_IDS)

    identities = {(world.geometry_id, world.truth_id) for world in worlds}
    assert identities == {
        (geometry, truth)
        for geometry in GEOMETRY_IDS
        for truth in TRUTH_IDS
    }

    expected = {
        "T0": ("B0", None),
        "TX": ("BX", ("BX", "B0")),
        "TC": ("BC", ("BC", "B0")),
    }
    for world in worlds:
        model_id, detectability = expected[world.truth_id]
        assert world.truth_model_id == model_id
        assert world.oracle_model_id == model_id
        assert world.detectability_reference == detectability


def test_amap1_truth_parameter_surface_matches_oracle_models():
    for fixture in make_amap1_fixtures():
        for truth_id, model_id in (("T0", "B0"), ("TX", "BX"), ("TC", "BC")):
            model = make_amap1_model(fixture, model_id)
            theta = amap1_truth_theta(
                fixture,
                model_id,
                innovation_seed=100 + TRUTH_IDS.index(truth_id),
            )["sp"]
            expected = {
                parameter
                for process in model.species["sp"]
                for parameter in process.priors()
            }
            assert set(theta) == expected


def test_amap1_field_truths_draw_fresh_latent_realizations():
    fixture = make_amap1_fixtures()[0]

    for model_id in ("BX", "BC"):
        first = amap1_truth_theta(
            fixture,
            model_id,
            innovation_seed=501,
        )["sp"]
        repeat = amap1_truth_theta(
            fixture,
            model_id,
            innovation_seed=501,
        )["sp"]
        second = amap1_truth_theta(
            fixture,
            model_id,
            innovation_seed=502,
        )["sp"]

        names = sorted(name for name in first if name.startswith("map_z_"))
        assert names
        assert [first[name] for name in names] == [
            repeat[name] for name in names
        ]
        assert [first[name] for name in names] != [
            second[name] for name in names
        ]
        assert first["map_sigma"] == second["map_sigma"] == pytest.approx(0.55)


def test_amap1_environment_is_not_a_trivial_coordinate_constant():
    for fixture in make_amap1_fixtures():
        by_space = {}
        for key, values in fixture.covariates.items():
            by_space.setdefault(key[0], values["mean_env"])
        values = tuple(by_space.values())
        assert max(values) - min(values) > 1.0
        assert math.isclose(
            sum(values) / len(values),
            0.0,
            abs_tol=1e-12,
        )
