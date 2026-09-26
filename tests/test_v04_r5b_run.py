from types import SimpleNamespace

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


def test_r5b_training_subset_contains_direct_state_calibration():
    from esdm.validate.v04_r2_run import _subset_model
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture

    fixture = build_v04_r5a_fixture(_sample_csv())
    model, _ = _subset_model(fixture, fixture.train_spaces, knockout=None)
    names = tuple(stream.name for stream in model.streams)

    assert names == (
        "opportunistic",
        "calibrated",
        "annotated",
        "state_calibration",
    )
    direct = {stream.name: stream for stream in model.streams}["state_calibration"]
    exposed = sum(
        1 for key in model.domain.keys if direct.effort.at(key) > 0.0
    )
    assert exposed == 432


def test_r5b_heldout_direct_calibration_is_zero_exposure():
    from esdm.validate.v04_r2_run import _subset_model
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture

    fixture = build_v04_r5a_fixture(_sample_csv())
    model, _ = _subset_model(fixture, fixture.heldout_spaces, knockout=None)
    direct = {stream.name: stream for stream in model.streams}["state_calibration"]

    assert all(direct.effort.at(key) == 0.0 for key in model.domain.keys)
