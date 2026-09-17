"""Historical v0.3 benchmark-shape checks.

The v0.3 promotion interpretation is retired in v0.3.1. These tests keep the historical
world declarations inspectable but do not treat the old knockout or misspecification
worlds as current promotion evidence.
"""


def test_v03_known_truth_suite_remains_inspectable_as_historical_four_world_universe():
    from esdm.validate.known_truth import make_v03_known_truth_worlds

    worlds = {world.name: world for world in make_v03_known_truth_worlds()}
    assert tuple(worlds) == (
        "correct_effort",
        "wrong_effort_geometry",
        "hidden_driver",
        "suitability_knockout",
    )
    for world in worlds.values():
        assert world.target_parameter.startswith("sp.suitability.")
        assert world.generating_model.domain.keys == world.fitting_model.domain.keys


def test_v03_wrong_effort_and_hidden_driver_are_recorded_as_misspecified_worlds():
    from esdm.validate.known_truth import make_v03_known_truth_worlds

    worlds = {world.name: world for world in make_v03_known_truth_worlds()}
    assert worlds["wrong_effort_geometry"].world_class == "misspecified"
    assert worlds["hidden_driver"].world_class == "misspecified"


def test_v03_knockout_world_is_historical_not_current_knockout_contract():
    from esdm.validate.known_truth import make_v03_known_truth_worlds

    world = {world.name: world for world in make_v03_known_truth_worlds()}[
        "suitability_knockout"
    ]
    assert world.world_class == "knockout"
    assert world.truth[world.target_parameter] == 0.0
