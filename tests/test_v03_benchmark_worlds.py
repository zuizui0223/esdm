def test_correct_effort_and_wrong_effort_worlds_share_ecological_truth():
    from esdm.simulate.benchmark_v03 import make_correct_effort_world, make_wrong_effort_world

    correct = make_correct_effort_world(seed=3)
    wrong = make_wrong_effort_world(seed=3)

    assert correct.truth_log_intensity == wrong.truth_log_intensity
    assert correct.true_effort == wrong.true_effort
    assert correct.fit_effort == correct.true_effort
    assert wrong.fit_effort != wrong.true_effort
    assert correct.counts == wrong.counts
    assert correct.kind == "in_model"
    assert wrong.kind == "misspecified"


def test_hidden_driver_world_omits_true_driver_from_fit_covariates():
    from esdm.simulate.benchmark_v03 import make_hidden_driver_world

    world = make_hidden_driver_world(seed=5)

    assert world.kind == "misspecified"
    assert "observed_env" in world.fit_covariates
    assert "hidden_env" not in world.fit_covariates
    assert any(abs(x) > 0 for x in world.hidden_log_contribution)


def test_knockout_world_has_no_suitability_effect_by_construction():
    from esdm.simulate.benchmark_v03 import make_knockout_world

    world = make_knockout_world(seed=7)

    assert world.kind == "in_model"
    assert world.truth_process_present is False
    assert max(world.truth_log_intensity) == min(world.truth_log_intensity)
