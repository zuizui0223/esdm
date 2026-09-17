def test_knockout_world_is_fit_with_nonknockout_suitability_model():
    from esdm.simulate.benchmark_v03 import make_knockout_world, fit_inputs_for_world

    world = make_knockout_world(seed=11)
    model, data, covariates = fit_inputs_for_world(world)

    process = model.species["species"][0]
    assert process.name == "suitability"
    assert process.priors()
    assert set(covariates[next(iter(covariates))]) == {"observed_env"}
    assert data == world.counts


def test_hidden_driver_fit_adapter_excludes_hidden_covariate():
    from esdm.simulate.benchmark_v03 import make_hidden_driver_world, fit_inputs_for_world

    world = make_hidden_driver_world(seed=13)
    model, _, covariates = fit_inputs_for_world(world)

    process = model.species["species"][0]
    assert process.covariates == ("observed_env",)
    assert all("hidden_env" not in row for row in covariates.values())
