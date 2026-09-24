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


def test_r6_null_truth_zeroes_only_activity_and_state_slopes():
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture
    from esdm.validate.v04_r6_matched import (
        R6_ACTIVITY_SLOPES,
        R6_STATE_SLOPES,
        r6_generating_theta,
    )

    fixture = build_v04_r5a_fixture(_sample_csv())
    structured = r6_generating_theta(fixture, "structured")
    null = r6_generating_theta(fixture, "resolution_null")

    for parameter in (*R6_ACTIVITY_SLOPES, *R6_STATE_SLOPES):
        assert structured["sp"][parameter] == fixture.generating_theta["sp"][parameter]
        assert null["sp"][parameter] == 0.0

    for parameter in (
        "intercept",
        "beta_precip",
        "beta_lat",
        "beta_eastness",
        "activity_intercept",
        "alpha_foraging",
    ):
        assert null["sp"][parameter] == structured["sp"][parameter]


def test_r6_collapsed_model_preserves_streams_but_removes_environmental_resolution():
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture
    from esdm.validate.v04_r6_matched import _subset_candidate_model

    fixture = build_v04_r5a_fixture(_sample_csv())
    full, _ = _subset_candidate_model(
        fixture, fixture.train_spaces, collapsed=False
    )
    collapsed, _ = _subset_candidate_model(
        fixture, fixture.train_spaces, collapsed=True
    )

    assert tuple(stream.name for stream in collapsed.streams) == tuple(
        stream.name for stream in full.streams
    )
    full_activity = full.species["sp"][1]
    collapsed_activity = collapsed.species["sp"][1]
    full_state = full.species["sp"][2]
    collapsed_state = collapsed.species["sp"][2]

    assert len(full_activity.priors()) == 5
    assert set(collapsed_activity.priors()) == {"activity_intercept"}
    assert len(full_state.priors()) == 5
    assert set(collapsed_state.priors()) == {"alpha_foraging"}


def test_r6_summary_keeps_worlds_separate_and_counts_two_fits_per_record():
    from esdm.validate.v04_r6_matched import V04R6Replicate, summarize_v04_r6

    rows = (
        V04R6Replicate("structured", 0, 1, -1.0, -1.02, 0, 0),
        V04R6Replicate("structured", 1, 2, -1.0, -1.01, 0, 0),
        V04R6Replicate("resolution_null", 0, 3, -1.0, -1.001, 0, 0),
        V04R6Replicate("resolution_null", 1, 4, -1.0, -0.999, 0, 0),
    )
    summary = summarize_v04_r6(rows)

    assert summary.total_fits == 8
    assert summary.worlds["structured"].mean_gain == pytest.approx(0.015)
    assert summary.worlds["resolution_null"].mean_gain == pytest.approx(0.0)
