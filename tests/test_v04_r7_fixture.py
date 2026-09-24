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


def test_r7_direct_and_passive_have_exact_equal_expected_label_budget():
    from esdm.validate.v04_r7_design import (
        R7_EXPECTED_LABEL_BUDGET,
        build_v04_r7_passive_fixture,
        expected_direct_labels,
    )

    text = _sample_csv()
    passive = build_v04_r7_passive_fixture(text)

    assert expected_direct_labels(text) == pytest.approx(R7_EXPECTED_LABEL_BUDGET)
    assert passive.expected_passive_labels == pytest.approx(R7_EXPECTED_LABEL_BUDGET)


def test_r7_passive_calibration_is_training_only_and_same_geometry():
    from esdm.validate.v04_r4a_design import build_v04_r4a_fixture
    from esdm.validate.v04_r7_design import build_v04_r7_passive_fixture

    text = _sample_csv()
    r4 = build_v04_r4a_fixture(text)
    passive = build_v04_r7_passive_fixture(text)
    stream = {
        stream.name: stream for stream in passive.model.streams
    }["passive_calibration"]

    train_exposed = {
        key for key in passive.model.domain.keys
        if key[0] in set(passive.train_spaces) and stream.effort.at(key) > 0.0
    }
    expected = {
        (space, doy, hour)
        for space in r4.annotated_spaces
        for doy, hour in r4.annotated_times
    }
    assert train_exposed == expected
    assert all(
        stream.effort.at(key) == 0.0
        for key in passive.model.domain.keys
        if key[0] in set(passive.heldout_spaces)
    )
