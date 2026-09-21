import math

import pytest

from esdm.observe import (
    EffortField,
    KnownDetection,
    LogitDetection,
    MultiLogLinearEffort,
)


def _sample_csv(rows=130):
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(rows):
        latitude = 22.0 + (i % 31) * 0.75
        longitude = -154.0 + (i % 43) * 2.25
        average = 45.0 + ((i * 7) % 29) * 1.3
        total19 = 35.0 + (i % 13) * 1.7
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.3f},{latitude:.4f},{longitude:.4f},ST,{total19:.1f}"
        )
    return "\n".join(lines) + "\n"


def _maximin_reference(train_spaces, covariates):
    points = {
        space: (
            covariates[(space, 15, 0)]["precip_z_train"],
            covariates[(space, 15, 0)]["eastness_z_train"],
        )
        for space in train_spaces
    }
    first = min(
        (
            (-((p * p) + (e * e)), space)
            for space, (p, e) in points.items()
        )
    )[1]
    selected = [first]
    remaining = set(train_spaces) - {first}
    while len(selected) < 18:
        scored = []
        for space in remaining:
            p, e = points[space]
            min_d2 = min(
                (p - points[other][0]) ** 2 + (e - points[other][1]) ** 2
                for other in selected
            )
            scored.append((-min_d2, space))
        chosen = min(scored)[1]
        selected.append(chosen)
        remaining.remove(chosen)
    return tuple(selected)


def test_r2_positive_fixture_has_three_streams_unknown_observation_and_time_truth():
    from esdm.validate.v04_r2_state_activity import (
        build_v04_r2_fixture,
    )

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    assert len(fixture.model.domain.keys) == 120 * 6 * 4
    assert len(fixture.calibration_spaces) == 18

    opportunistic, calibrated, annotated = fixture.model.streams
    assert isinstance(opportunistic.effort, MultiLogLinearEffort)
    assert isinstance(opportunistic.detection, LogitDetection)
    assert set(opportunistic.priors()) == {
        "gamma_precip",
        "gamma_season",
        "gamma_hour",
        "detection_intercept",
    }
    assert isinstance(calibrated.effort, EffortField)
    assert calibrated.detection_probability == 0.90
    assert isinstance(annotated.effort, EffortField)
    assert isinstance(annotated.detection, KnownDetection)
    assert annotated.detection.probability({}) == pytest.approx(0.85)

    theta = fixture.generating_theta["sp"]
    assert theta["activity_beta_season"] == 0.55
    assert theta["activity_beta_hour"] == 0.40
    assert theta["beta_foraging_season"] == 0.50
    assert theta["beta_foraging_hour"] == -0.45

    obs = fixture.generating_theta_obs["opportunistic"]
    assert obs == {
        "gamma_precip": 0.35,
        "gamma_season": 0.30,
        "gamma_hour": -0.25,
        "detection_intercept": -0.20,
    }


def test_r2_temporal_covariates_are_deterministic_and_nonconstant():
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    space = fixture.train_spaces[0]

    at_15_0 = fixture.covariates[(space, 15, 0)]
    at_15_6 = fixture.covariates[(space, 15, 6)]
    at_75_0 = fixture.covariates[(space, 75, 0)]

    assert at_15_0["season_sin"] == pytest.approx(0.0)
    assert at_15_0["season_cos"] == pytest.approx(1.0)
    assert at_15_0["hour_sin"] == pytest.approx(0.0)
    assert at_15_0["hour_cos"] == pytest.approx(1.0)
    assert at_15_6["hour_sin"] == pytest.approx(1.0)
    assert at_15_6["hour_cos"] == pytest.approx(0.0, abs=1e-12)
    assert at_75_0["season_sin"] != pytest.approx(at_15_0["season_sin"])


def test_r2_positive_calibration_is_deterministic_maximin_and_exposure_is_partial():
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    expected = _maximin_reference(fixture.train_spaces, fixture.covariates)
    assert fixture.calibration_spaces == expected

    _opportunistic, calibrated, annotated = fixture.model.streams
    calibration = fixture.calibration_spaces[0]
    heldout = fixture.heldout_spaces[0]
    uncalibrated = next(
        space
        for space in fixture.train_spaces
        if space not in set(fixture.calibration_spaces)
    )

    assert calibrated.effort.at((calibration, 15, 0)) == 3.0
    assert calibrated.effort.at((uncalibrated, 15, 0)) == 0.0
    assert calibrated.effort.at((heldout, 15, 0)) == 0.0

    assert annotated.effort.at((calibration, 15, 0)) == 8.0
    assert annotated.effort.at((uncalibrated, 15, 0)) == 0.0
    assert annotated.effort.at((heldout, 15, 0)) == 8.0


def test_r2_sparse_profile_selects_four_center_spaces_only():
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture

    fixture = build_v04_r2_fixture(_sample_csv(), profile="sparse")
    scored = []
    for space in fixture.train_spaces:
        values = fixture.covariates[(space, 15, 0)]
        scored.append(
            (
                values["precip_z_train"] ** 2
                + values["eastness_z_train"] ** 2,
                space,
            )
        )
    assert fixture.calibration_spaces == tuple(
        space for _, space in sorted(scored)[:4]
    )


def test_r2_truth_and_identification_anchors_match_frozen_gate():
    from esdm.validate.v04_r2_state_activity import (
        build_v04_r2_fixture,
        v04_r2_identification_anchors,
    )

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    theta = fixture.generating_theta["sp"]
    assert theta == {
        "intercept": -2.0,
        "beta_precip": 0.45,
        "beta_lat": -0.20,
        "beta_eastness": 0.35,
        "activity_intercept": -0.35,
        "activity_beta_precip": 0.50,
        "activity_beta_eastness": 0.35,
        "activity_beta_season": 0.55,
        "activity_beta_hour": 0.40,
        "alpha_foraging": 0.20,
        "beta_foraging_precip": -0.45,
        "beta_foraging_eastness": 0.40,
        "beta_foraging_season": 0.50,
        "beta_foraging_hour": -0.45,
    }

    anchors = v04_r2_identification_anchors(fixture)
    assert len(anchors) == 3
    assert anchors[1][0]["sp"]["activity_beta_season"] == 0.30
    assert anchors[1][1]["opportunistic"]["gamma_precip"] == 0.10
    assert anchors[1][1]["opportunistic"]["detection_intercept"] == -0.70
    assert anchors[2][0]["sp"]["beta_foraging_hour"] == -0.20
    assert anchors[2][1]["opportunistic"]["gamma_hour"] == -0.50


def test_r2_unknown_annotation_detection_refusal_is_intercept_only():
    from esdm.validate.v04_r2_state_activity import (
        build_v04_r2_unknown_detection_fixture,
        v04_r2_unknown_detection_anchors,
    )

    fixture = build_v04_r2_unknown_detection_fixture(_sample_csv())
    activity = fixture.model.species["sp"][1]
    annotated = fixture.model.streams[2]

    assert activity.covariates == ()
    assert set(activity.priors()) == {"activity_intercept"}
    assert isinstance(annotated.detection, LogitDetection)
    assert fixture.generating_theta["sp"]["activity_intercept"] == -0.35
    assert fixture.generating_theta_obs["annotated"] == {
        "detection_intercept": 0.40
    }

    anchors = v04_r2_unknown_detection_anchors(fixture)
    assert len(anchors) == 3
    assert anchors[1][0]["sp"]["activity_intercept"] == 0.20
    assert anchors[1][1]["annotated"]["detection_intercept"] == -0.30
    assert anchors[2][0]["sp"]["activity_intercept"] == -0.90
    assert anchors[2][1]["annotated"]["detection_intercept"] == 0.90


def test_r2_eastness_is_true_extrapolation():
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    train = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.train_spaces
    ]
    heldout = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.heldout_spaces
    ]
    assert min(heldout) > max(train)
