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


def test_r5a_adds_one_state_only_calibration_stream():
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture

    fixture = build_v04_r5a_fixture(_sample_csv())
    streams = {stream.name: stream for stream in fixture.model.streams}

    assert tuple(streams) == (
        "opportunistic",
        "calibrated",
        "annotated",
        "state_calibration",
    )
    direct = streams["state_calibration"]
    assert direct.consumes == frozenset({"state"})
    assert direct.informs == frozenset({"state"})
    assert direct.priors() == {}


def test_r5a_state_calibration_is_exactly_one_expected_label_per_r4_context():
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture

    fixture = build_v04_r5a_fixture(_sample_csv())
    direct = {stream.name: stream for stream in fixture.model.streams}["state_calibration"]
    train = set(fixture.train_spaces)

    exposed = {
        key
        for key in fixture.model.domain.keys
        if key[0] in train and direct.effort.at(key) > 0.0
    }
    expected = {
        (space, doy, hour)
        for space in fixture.annotated_spaces
        for doy, hour in fixture.annotated_times
    }

    assert exposed == expected
    assert len(exposed) == 432
    assert sum(direct.effort.at(key) for key in exposed) == 432.0
    assert all(direct.effort.at(key) == 1.0 for key in exposed)


def test_r5a_direct_state_calibration_has_no_heldout_exposure():
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture

    fixture = build_v04_r5a_fixture(_sample_csv())
    direct = {stream.name: stream for stream in fixture.model.streams}["state_calibration"]

    assert all(
        direct.effort.at(key) == 0.0
        for key in fixture.model.domain.keys
        if key[0] in set(fixture.heldout_spaces)
    )


def test_r5a_preserves_r4_existing_stream_geometry_and_truth():
    from esdm.validate.v04_r4a_design import build_v04_r4a_fixture
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture

    text = _sample_csv()
    r4 = build_v04_r4a_fixture(text)
    r5 = build_v04_r5a_fixture(text)

    assert r5.train_spaces == r4.train_spaces
    assert r5.heldout_spaces == r4.heldout_spaces
    assert r5.calibrated_spaces == r4.calibrated_spaces
    assert r5.annotated_spaces == r4.annotated_spaces
    assert r5.annotated_times == r4.annotated_times
    assert r5.covariates == r4.covariates
    assert r5.generating_theta == r4.generating_theta
    for name in r4.generating_theta_obs:
        assert r5.generating_theta_obs[name] == r4.generating_theta_obs[name]
