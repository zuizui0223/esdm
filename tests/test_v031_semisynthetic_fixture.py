from pathlib import Path

from esdm.validate.v031_semisynthetic import (
    V031_SEMISYNTHETIC_MANIFEST,
    build_v031_semisynthetic_fixture,
    parse_station_csv,
)


def _sample_csv(rows=120):
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(rows):
        latitude = 20.0 + (i % 30) * 0.8
        longitude = -155.0 + (i % 40) * 2.3
        average = 40.0 + (i % 17) * 2.1
        total19 = 35.0 + (i % 13) * 1.7
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.1f},{latitude:.4f},{longitude:.4f},ST,{total19:.1f}"
        )
    return "\n".join(lines) + "\n"


def test_manifest_pins_external_source_and_selection_before_outcomes():
    manifest = V031_SEMISYNTHETIC_MANIFEST
    assert manifest.source_commit == "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a"
    assert manifest.source_path == "rain/annual_precipitation.csv"
    assert manifest.station_rows == 120
    assert manifest.doy_bins == (15, 75, 135, 195, 255, 315)
    assert manifest.hour_bins == (0, 6, 12, 18)
    assert manifest.heldout_block == "east"


def test_station_parser_applies_frozen_first_120_rule():
    stations = parse_station_csv(_sample_csv(130), rows=120)
    assert len(stations) == 120
    assert stations[0].station_id == "S0000"
    assert stations[-1].station_id == "S0119"


def test_semisynthetic_fixture_uses_real_geometry_shape_and_temporal_axes():
    fixture = build_v031_semisynthetic_fixture(_sample_csv(130))
    assert len(fixture.stations) == 120
    assert len(fixture.model.domain.space) == 120
    assert len(fixture.model.domain.doy) == 6
    assert len(fixture.model.domain.hour) == 4
    assert len(fixture.model.domain.keys) == 120 * 6 * 4
    assert set(fixture.spatial_blocks) == {"west", "central", "east"}
    assert fixture.heldout_block == "east"
    assert len(fixture.train_spaces) + len(fixture.heldout_spaces) == 120
    assert len(fixture.heldout_spaces) > 0


def test_effort_varies_in_space_season_and_hour_and_is_not_precipitation_itself():
    fixture = build_v031_semisynthetic_fixture(_sample_csv(130))
    stream = fixture.model.streams[0]
    first_space = fixture.model.domain.space[0]
    same_station = [
        stream.effort.at(key)
        for key in fixture.model.domain.keys
        if key[0] == first_space
    ]
    assert len(set(round(value, 8) for value in same_station)) > 4

    precip = []
    effort = []
    for space in fixture.model.domain.space:
        key = (space, fixture.model.domain.doy[0], fixture.model.domain.hour[0])
        precip.append(fixture.covariates[key]["precip_z"])
        effort.append(stream.effort.at(key))
    ratios = [e / (abs(p) + 1.0) for e, p in zip(effort, precip)]
    assert len(set(round(value, 6) for value in ratios)) > 20
