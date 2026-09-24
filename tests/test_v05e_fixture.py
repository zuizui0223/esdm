import pytest


def test_v05e_world_truths_cross_beta_and_event_evidence():
    from esdm.validate.v05e_fixture import build_v05e_fixture

    hidden = build_v05e_fixture("hidden_event_silent")
    realized = build_v05e_fixture("realized_only")
    directed = build_v05e_fixture("directed_realized")

    assert hidden.generating_theta["focal"]["beta_partner"] == 0.0
    assert hidden.generating_theta_obs["events"]["event_intercept"] == -8.0
    assert "hidden_shared" in next(iter(hidden.generating_covariates.values()))
    assert "hidden_shared" not in next(iter(hidden.fitting_covariates.values()))

    assert realized.generating_theta["focal"]["beta_partner"] == 0.0
    assert realized.generating_theta_obs["events"]["event_intercept"] == -1.0

    assert directed.generating_theta["focal"]["beta_partner"] == pytest.approx(0.75)
    assert directed.generating_theta_obs["events"]["event_intercept"] == -1.0


def test_v05e_pair_event_exposure_is_training_only():
    from esdm.validate.v05e_fixture import build_v05e_fixture

    fixture = build_v05e_fixture("directed_realized")
    events = {stream.name: stream for stream in fixture.fitting_model.streams}["events"]
    train = set(fixture.train_spaces)
    heldout = set(fixture.heldout_spaces)

    assert all(
        events.effort.at(key) > 0.0
        for key in fixture.fitting_model.domain.keys
        if key[0] in train
    )
    assert all(
        events.effort.at(key) == 0.0
        for key in fixture.fitting_model.domain.keys
        if key[0] in heldout
    )
