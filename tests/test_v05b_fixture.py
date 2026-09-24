def test_v05b_generating_world_adds_hidden_driver_but_zero_partner_effect():
    from esdm.validate.v05b_hidden_driver import build_v05b_fixture

    fixture = build_v05b_fixture()

    assert fixture.generating_theta["focal"]["beta_partner"] == 0.0
    assert fixture.generating_theta["source"]["beta_source_hidden"] == 0.90
    assert fixture.generating_theta["focal"]["beta_focal_hidden"] == 0.90
    assert all(
        "hidden_shared" in values
        for values in fixture.generating_covariates.values()
    )
    assert all(
        "hidden_shared" not in values
        for values in fixture.fitting_covariates.values()
    )


def test_v05b_fitting_model_is_exact_v05a_model_class():
    from esdm.validate.v05a_directed import build_v05a_fixture
    from esdm.validate.v05b_hidden_driver import build_v05b_fixture

    a = build_v05a_fixture()
    b = build_v05b_fixture()

    assert a.model.species == b.fitting_model.species
    assert a.model.streams == b.fitting_model.streams
    assert a.train_spaces == b.train_spaces
    assert a.heldout_spaces == b.heldout_spaces
