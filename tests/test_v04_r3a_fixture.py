def _sample_csv(rows=130):
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(rows):
        latitude = 22.0 + (i % 31) * 0.75
        longitude = -154.0 + (i % 43) * 2.25
        average = 45.0 + ((i * 7) % 29) * 1.3
        total19 = 35.0 + (i % 13) * 1.7
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.3f},"
            f"{latitude:.4f},{longitude:.4f},ST,{total19:.1f}"
        )
    return "\n".join(lines) + "\n"


def test_r3a_positive_budget_is_exactly_36_by_12():
    from esdm.validate.v04_r3a_design import build_v04_r3a_fixture

    fixture = build_v04_r3a_fixture(_sample_csv())

    assert len(fixture.annotated_spaces) == 36
    assert len(fixture.annotated_times) == 12
    annotated = fixture.model.streams[2]
    train = set(fixture.train_spaces)
    exposed = {
        key
        for key in fixture.model.domain.keys
        if key[0] in train and annotated.effort.at(key) > 0.0
    }
    expected = {
        (space, doy, hour)
        for space in fixture.annotated_spaces
        for doy, hour in fixture.annotated_times
    }
    assert exposed == expected
    assert len(exposed) == 432


def test_r3a_calibrated_presence_only_remains_r2_18_by_24():
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture
    from esdm.validate.v04_r3a_design import build_v04_r3a_fixture

    text = _sample_csv()
    r2 = build_v04_r2_fixture(text, profile="positive")
    r3 = build_v04_r3a_fixture(text)

    assert r3.calibrated_spaces == r2.calibration_spaces
    assert r3.annotated_spaces[:18] == r2.calibration_spaces

    calibrated = r3.model.streams[1]
    exposed = {
        key
        for key in r3.model.domain.keys
        if calibrated.effort.at(key) > 0.0
    }
    expected = {
        (space, doy, hour)
        for space in r3.calibrated_spaces
        for doy in r3.model.domain.doy
        for hour in r3.model.domain.hour
    }
    assert exposed == expected
    assert len(exposed) == 18 * 24


def test_r3a_changes_only_positive_annotated_training_geometry():
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture
    from esdm.validate.v04_r3a_design import build_v04_r3a_fixture

    text = _sample_csv()
    r2 = build_v04_r2_fixture(text, profile="positive")
    r3 = build_v04_r3a_fixture(text)

    assert r3.train_spaces == r2.train_spaces
    assert r3.heldout_spaces == r2.heldout_spaces
    assert r3.covariates == r2.covariates
    assert r3.generating_theta == r2.generating_theta
    assert r3.generating_theta_obs == r2.generating_theta_obs

    r2_opportunistic, r2_calibrated, _ = r2.model.streams
    r3_opportunistic, r3_calibrated, r3_annotated = r3.model.streams

    assert r3_opportunistic.priors() == r2_opportunistic.priors()
    assert r3_calibrated.priors() == r2_calibrated.priors()
    assert r3_annotated.detection.probability({}) == 0.85


def test_r3a_east_annotations_exist_for_future_evaluation_but_not_training_budget():
    from esdm.validate.v04_r3a_design import build_v04_r3a_fixture

    fixture = build_v04_r3a_fixture(_sample_csv())
    annotated = fixture.model.streams[2]
    heldout = set(fixture.heldout_spaces)

    heldout_exposed = {
        key
        for key in fixture.model.domain.keys
        if key[0] in heldout and annotated.effort.at(key) > 0.0
    }
    assert heldout_exposed == {
        (space, doy, hour)
        for space in fixture.heldout_spaces
        for doy in fixture.model.domain.doy
        for hour in fixture.model.domain.hour
    }

    train_exposed = {
        key
        for key in fixture.model.domain.keys
        if key[0] in set(fixture.train_spaces)
        and annotated.effort.at(key) > 0.0
    }
    assert len(train_exposed) == 432
    assert not (train_exposed & heldout_exposed)


def test_r3a_selected_temporal_contexts_are_declared_domain_contexts():
    from esdm.validate.v04_r3a_design import build_v04_r3a_fixture

    fixture = build_v04_r3a_fixture(_sample_csv())

    assert set(fixture.annotated_times) <= {
        (doy, hour)
        for doy in fixture.model.domain.doy
        for hour in fixture.model.domain.hour
    }
    assert fixture.annotated_times[0] == (15, 0)
