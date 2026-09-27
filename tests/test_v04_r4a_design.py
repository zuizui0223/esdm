import pytest


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


def test_r4a_phase_balance_is_exact_three_by_four_cartesian_product():
    from esdm.validate.v04_r4a_design import phase_balanced_temporal_contexts

    selected = phase_balanced_temporal_contexts(
        (15, 75, 135, 195, 255, 315),
        (0, 6, 12, 18),
    )

    assert selected == (
        (15, 0), (15, 6), (15, 12), (15, 18),
        (135, 0), (135, 6), (135, 12), (135, 18),
        (255, 0), (255, 6), (255, 12), (255, 18),
    )
    assert {doy: sum(row[0] == doy for row in selected) for doy in (15, 135, 255)} == {
        15: 4,
        135: 4,
        255: 4,
    }
    assert {hour: sum(row[1] == hour for row in selected) for hour in (0, 6, 12, 18)} == {
        0: 3,
        6: 3,
        12: 3,
        18: 3,
    }


@pytest.mark.parametrize(
    ("doys", "hours"),
    [
        ((15, 75, 135, 195, 255), (0, 6, 12, 18)),
        ((15, 75, 135, 195, 255, 315), (0, 6, 12)),
        ((15, 75, 135, 195, 255, 255), (0, 6, 12, 18)),
        ((15, 75, 135, 195, 255, 315), (0, 6, 12, 12)),
    ],
)
def test_r4a_phase_balance_fails_closed_on_wrong_domain(doys, hours):
    from esdm.validate.v04_r4a_design import phase_balanced_temporal_contexts

    with pytest.raises(ValueError, match="R4 temporal design requires"):
        phase_balanced_temporal_contexts(doys, hours)


def test_r4a_positive_budget_is_exactly_36_by_12():
    from esdm.validate.v04_r4a_design import build_v04_r4a_fixture

    fixture = build_v04_r4a_fixture(_sample_csv())
    annotated = fixture.model.streams[2]
    train = set(fixture.train_spaces)
    exposed = {
        key
        for key in fixture.model.domain.keys
        if key[0] in train and annotated.effort.at(key) > 0.0
    }

    assert len(fixture.annotated_spaces) == 36
    assert len(fixture.annotated_times) == 12
    assert len(exposed) == 432
    assert exposed == {
        (space, doy, hour)
        for space in fixture.annotated_spaces
        for doy, hour in fixture.annotated_times
    }


def test_r4a_isolates_temporal_design_from_r3a():
    from esdm.validate.v04_r3a_design import build_v04_r3a_fixture
    from esdm.validate.v04_r4a_design import build_v04_r4a_fixture

    text = _sample_csv()
    r3 = build_v04_r3a_fixture(text)
    r4 = build_v04_r4a_fixture(text)

    assert r4.train_spaces == r3.train_spaces
    assert r4.heldout_spaces == r3.heldout_spaces
    assert r4.calibrated_spaces == r3.calibrated_spaces
    assert r4.annotated_spaces == r3.annotated_spaces
    assert r4.covariates == r3.covariates
    assert r4.generating_theta == r3.generating_theta
    assert r4.generating_theta_obs == r3.generating_theta_obs
    assert r4.annotated_times != r3.annotated_times


def test_r4a_calibrated_and_heldout_exposure_remain_unchanged():
    from esdm.validate.v04_r4a_design import build_v04_r4a_fixture

    fixture = build_v04_r4a_fixture(_sample_csv())
    calibrated = fixture.model.streams[1]
    annotated = fixture.model.streams[2]

    calibrated_exposed = {
        key
        for key in fixture.model.domain.keys
        if calibrated.effort.at(key) > 0.0
    }
    assert len(calibrated_exposed) == 18 * 24

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
