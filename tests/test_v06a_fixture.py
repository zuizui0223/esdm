import pytest


def test_v06a_direct_accessibility_is_training_only():
    from esdm.validate.v06a_fixture import build_v06a_fixture

    fixture = build_v06a_fixture()
    access = {stream.name: stream for stream in fixture.model.streams}["access"]
    train = set(fixture.train_spaces)
    heldout = set(fixture.heldout_spaces)

    assert len(train) == 24
    assert len(heldout) == 12
    assert all(
        access.effort.at(key) == 20.0
        for key in fixture.model.domain.keys
        if key[0] in train
    )
    assert all(
        access.effort.at(key) == 0.0
        for key in fixture.model.domain.keys
        if key[0] in heldout
    )


def test_v06a_truth_has_distinct_suitability_and_accessibility_gradients():
    from esdm.validate.v06a_fixture import (
        V06A_RECOVERY_TRUTH,
        build_v06a_fixture,
    )

    fixture = build_v06a_fixture()
    assert V06A_RECOVERY_TRUTH["sp.suitability.beta_habitat"] == pytest.approx(0.75)
    assert V06A_RECOVERY_TRUTH["sp.accessibility.beta_distance"] == pytest.approx(-1.10)
    assert tuple(stream.name for stream in fixture.model.streams) == ("joint", "access")
