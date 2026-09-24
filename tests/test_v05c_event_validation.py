import pytest


def test_v05c_worlds_freeze_event_probabilities_and_training_only_effort():
    from esdm.validate.v05c_event_validation import (
        build_v05c_world,
        expected_training_events,
    )

    true = build_v05c_world("interaction_event")
    null = build_v05c_world("hidden_driver_null")

    assert true.true_event_probability == pytest.approx(0.25)
    assert null.true_event_probability == pytest.approx(0.005)
    assert true.generating_theta["focal"]["beta_partner"] == pytest.approx(0.75)
    assert null.generating_theta["focal"]["beta_partner"] == 0.0

    for fixture in (true, null):
        stream = {
            stream.name: stream
            for stream in fixture.fitting_model.streams
        }["interaction_events"]
        assert all(
            stream.effort.at(key) == pytest.approx(0.5)
            for key in fixture.fitting_model.domain.keys
            if key[0] in set(fixture.train_spaces)
        )
        assert all(
            stream.effort.at(key) == 0.0
            for key in fixture.fitting_model.domain.keys
            if key[0] in set(fixture.heldout_spaces)
        )

    assert expected_training_events(true) > expected_training_events(null)


def test_v05c_hidden_world_keeps_event_parameter_distinct_from_beta():
    from esdm.validate.v05c_event_validation import build_v05c_world

    fixture = build_v05c_world("hidden_driver_null")
    event = {
        stream.name: stream
        for stream in fixture.fitting_model.streams
    }["interaction_events"]

    assert event.event_logit_parameter == "event_logit"
    assert "beta_partner" not in event.priors()
