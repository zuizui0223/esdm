import pytest


def test_v05a_fixture_has_measured_shared_environment_and_fresh_null():
    from esdm.validate.v05a_directed import build_v05a_fixture, v05a_theta

    fixture = build_v05a_fixture()
    positive = v05a_theta(fixture, "interaction")
    null = v05a_theta(fixture, "measured_shared_null")

    assert len(fixture.train_spaces) == 24
    assert len(fixture.heldout_spaces) == 12
    assert positive["focal"]["beta_partner"] == pytest.approx(0.75)
    assert null["focal"]["beta_partner"] == 0.0
    assert positive["source"] == null["source"]
    for parameter in ("focal_intercept", "beta_focal_driver", "beta_focal_shared"):
        assert positive["focal"][parameter] == null["focal"][parameter]
    assert all(
        {"shared_env", "source_driver", "focal_driver"}
        <= set(values)
        for values in fixture.covariates.values()
    )


def test_v05a_focal_depends_on_source_latent_not_source_records():
    from esdm.validate.v05a_directed import build_v05a_fixture

    fixture = build_v05a_fixture()
    partner = fixture.model.species["focal"][1]

    assert partner.source_species == "source"
    assert partner.latent_species_dependencies == frozenset({"source"})
    assert tuple(stream.name for stream in fixture.model.streams) == (
        "source_records",
        "focal_records",
    )
