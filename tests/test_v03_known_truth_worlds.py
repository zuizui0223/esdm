import math


def test_v03_known_truth_suite_has_four_generic_worlds():
    from esdm.validate.known_truth import make_v03_known_truth_worlds

    worlds = {world.name: world for world in make_v03_known_truth_worlds()}
    assert tuple(worlds) == (
        "correct_effort",
        "wrong_effort_geometry",
        "hidden_driver",
        "suitability_knockout",
    )

    for world in worlds.values():
        world.generating_model.check_design()
        world.fitting_model.check_design()
        assert world.target_parameter.startswith("sp.suitability.")
        assert world.generating_model.domain.keys == world.fitting_model.domain.keys


def test_wrong_effort_world_changes_observation_geometry_not_ecological_truth():
    from esdm.validate.known_truth import make_v03_known_truth_worlds

    worlds = {world.name: world for world in make_v03_known_truth_worlds()}
    world = worlds["wrong_effort_geometry"]

    generating_stream = world.generating_model.streams[0]
    fitting_stream = world.fitting_model.streams[0]
    true_effort = tuple(generating_stream.effort.at(key) for key in world.generating_model.domain.keys)
    fit_effort = tuple(fitting_stream.effort.at(key) for key in world.fitting_model.domain.keys)

    assert true_effort != fit_effort
    assert len(set(fit_effort)) == 1
    assert world.truth[world.target_parameter] == 0.6
    assert world.expected_apparent_value > world.truth[world.target_parameter]


def test_hidden_driver_world_omits_one_generating_covariate_from_fit():
    from esdm.validate.known_truth import make_v03_known_truth_worlds

    worlds = {world.name: world for world in make_v03_known_truth_worlds()}
    world = worlds["hidden_driver"]
    generating_process = world.generating_model.species["sp"][0]
    fitting_process = world.fitting_model.species["sp"][0]

    assert generating_process.requires == frozenset({"x", "hidden"})
    assert fitting_process.requires == frozenset({"x"})
    assert world.expected_apparent_value > world.truth[world.target_parameter]


def test_suitability_knockout_generates_no_environmental_gradient():
    from esdm.process import NoEffectProcess
    from esdm.validate.known_truth import make_v03_known_truth_worlds

    worlds = {world.name: world for world in make_v03_known_truth_worlds()}
    world = worlds["suitability_knockout"]

    assert isinstance(world.generating_model.species["sp"][0], NoEffectProcess)
    assert world.truth[world.target_parameter] == 0.0
    fields = world.generating_model.latent_fields(
        world.generating_theta,
        world.generating_covariates,
    )
    values = tuple(fields.log_intensity["sp"].values())
    assert all(math.isclose(value, 0.0, abs_tol=1e-12) for value in values)
