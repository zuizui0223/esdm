import math


def test_v05b_hidden_driver_is_unobserved_and_partly_tracks_source_driver():
    from esdm.validate.v05b_hidden import build_v05b_fixture

    fixture = build_v05b_fixture()
    keys = fixture.fitting_model.domain.keys
    source = [fixture.fitting_covariates[key]["source_driver"] for key in keys]
    hidden = [fixture.generating_covariates[key]["hidden_driver"] for key in keys]

    assert all(
        "hidden_driver" not in fixture.fitting_covariates[key]
        for key in keys
    )
    assert all(
        "hidden_driver" in fixture.generating_covariates[key]
        for key in keys
    )
    mean_s = sum(source) / len(source)
    mean_h = sum(hidden) / len(hidden)
    cov = sum((s - mean_s) * (h - mean_h) for s, h in zip(source, hidden))
    var_s = sum((s - mean_s) ** 2 for s in source)
    var_h = sum((h - mean_h) ** 2 for h in hidden)
    corr = cov / math.sqrt(var_s * var_h)

    assert 0.4 < corr < 0.99
    assert fixture.generating_theta["focal"]["beta_partner"] == 0.0


def test_v05b_fitting_model_is_exact_v05a_model():
    from esdm.validate.v05a_directed import build_v05a_fixture
    from esdm.validate.v05b_hidden import build_v05b_fixture

    a = build_v05a_fixture()
    b = build_v05b_fixture()

    assert b.fitting_model.species == a.model.species
    assert tuple(stream.name for stream in b.fitting_model.streams) == tuple(
        stream.name for stream in a.model.streams
    )
