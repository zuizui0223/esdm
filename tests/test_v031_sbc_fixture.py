from esdm.identify import IdentificationStatus, identify_parameter_from_design
from esdm.validate.v031_sbc_fixture import make_v031_sbc_fixture


def test_v031_sbc_fixture_identifies_every_free_parameter_before_sbc():
    fixture = make_v031_sbc_fixture()
    targets = (
        "sp.suitability.intercept",
        "sp.suitability.beta_x",
        "stream.opportunistic.gamma_x",
    )
    for target in targets:
        result = identify_parameter_from_design(
            fixture.model,
            fixture.covariates,
            theta=fixture.reference_theta,
            theta_obs=fixture.reference_theta_obs,
            target=target,
        )
        assert result.status is IdentificationStatus.IDENTIFIED


def test_v031_sbc_fixture_has_unknown_and_calibrated_effort_streams():
    fixture = make_v031_sbc_fixture()
    streams = {stream.name: stream for stream in fixture.model.streams}
    assert tuple(streams) == ("opportunistic", "calibrated")
    assert set(streams["opportunistic"].priors()) == {"gamma_x"}
    assert streams["calibrated"].priors() == {}
    assert all(stream.targets == frozenset({"sp"}) for stream in streams.values())
