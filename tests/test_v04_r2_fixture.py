import math

from esdm.observe import (
    EffortField,
    KnownDetection,
    LogitDetection,
    LogLinearEffort,
)
from esdm.process import LinearActivity, LinearSuitability


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


def test_r2_positive_fixture_has_four_streams_unknown_observation_and_temporal_truth():
    from esdm.validate.v04_state_activity_r2 import build_v04_r2_fixture

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")

    assert len(fixture.model.domain.keys) == 120 * 6 * 4
    assert len(fixture.presence_calibration_spaces) == 12
    assert len(fixture.annotation_calibration_spaces) == 18
    assert fixture.profile == "positive"

    names = tuple(stream.name for stream in fixture.model.streams)
    assert names == (
        "presence_opportunistic",
        "presence_calibrated",
        "annotated_opportunistic",
        "annotated_calibrated",
    )

    presence_opp, presence_cal, annotated_opp, annotated_cal = fixture.model.streams
    assert isinstance(presence_opp.effort, LogLinearEffort)
    assert presence_opp.effort.baseline == 4.0
    assert presence_opp.effort.covariate == "season_sin"
    assert presence_opp.effort.coefficient_parameter == "gamma_presence_season"
    assert isinstance(presence_cal.effort, EffortField)

    assert isinstance(annotated_opp.effort, LogLinearEffort)
    assert annotated_opp.effort.baseline == 6.0
    assert annotated_opp.effort.covariate == "diurnal_cos"
    assert annotated_opp.effort.coefficient_parameter == "gamma_annotation_diurnal"
    assert isinstance(annotated_opp.detection, LogitDetection)
    assert isinstance(annotated_cal.effort, EffortField)
    assert isinstance(annotated_cal.detection, KnownDetection)
    assert annotated_cal.detection.probability({}) == 0.85

    first_space = fixture.train_spaces[0]
    cov_15_0 = fixture.covariates[(first_space, 15, 0)]
    cov_15_6 = fixture.covariates[(first_space, 15, 6)]
    cov_75_0 = fixture.covariates[(first_space, 75, 0)]

    assert cov_15_0["season_sin"] == 0.0
    assert cov_15_0["season_cos"] == 1.0
    assert cov_15_0["diurnal_sin"] == 0.0
    assert cov_15_0["diurnal_cos"] == 1.0
    assert cov_15_6["diurnal_sin"] == 1.0
    assert abs(cov_15_6["diurnal_cos"]) < 1e-12
    assert cov_75_0["season_sin"] == math.sin(2.0 * math.pi * 60.0 / 365.0)

    assert fixture.generating_theta["sp"] == {
        "intercept": -2.0,
        "beta_precip": 0.45,
        "beta_lat": -0.20,
        "beta_eastness": 0.35,
        "beta_season": 0.30,
        "activity_intercept": -0.35,
        "activity_beta_precip": 0.40,
        "activity_beta_eastness": 0.30,
        "activity_beta_season": 0.50,
        "activity_beta_diurnal": 0.45,
        "alpha_foraging": 0.20,
        "beta_foraging_precip": -0.35,
        "beta_foraging_eastness": 0.40,
        "beta_foraging_season": -0.50,
        "beta_foraging_diurnal": 0.55,
    }
    assert fixture.generating_theta_obs == {
        "presence_opportunistic": {"gamma_presence_season": 0.35},
        "presence_calibrated": {},
        "annotated_opportunistic": {
            "gamma_annotation_diurnal": 0.30,
            "detection_intercept": 0.40,
        },
        "annotated_calibrated": {},
    }


def test_r2_calibrated_streams_are_partial_and_have_zero_east_exposure():
    from esdm.validate.v04_state_activity_r2 import build_v04_r2_fixture

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    _, presence_cal, _, annotated_cal = fixture.model.streams

    p_space = fixture.presence_calibration_spaces[0]
    a_space = fixture.annotation_calibration_spaces[0]
    east_space = fixture.heldout_spaces[0]

    assert presence_cal.effort.at((p_space, 15, 0)) == 3.0
    assert annotated_cal.effort.at((a_space, 15, 0)) == 5.0
    assert presence_cal.effort.at((east_space, 15, 0)) == 0.0
    assert annotated_cal.effort.at((east_space, 15, 0)) == 0.0

    train_eastness = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.train_spaces
    ]
    heldout_eastness = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.heldout_spaces
    ]
    assert min(heldout_eastness) > max(train_eastness)


def test_r2_presence_effort_refusal_is_isolated_presence_submodel():
    from esdm.validate.v04_state_activity_r2 import (
        build_v04_r2_fixture,
        v04_r2_presence_refusal_anchors,
    )

    fixture = build_v04_r2_fixture(
        _sample_csv(),
        profile="presence_effort_refusal",
    )

    assert len(fixture.model.species["sp"]) == 1
    assert isinstance(fixture.model.species["sp"][0], LinearSuitability)
    assert tuple(stream.name for stream in fixture.model.streams) == (
        "presence_opportunistic",
    )
    assert fixture.generating_theta["sp"] == {
        "intercept": -2.0,
        "beta_precip": 0.45,
        "beta_lat": -0.20,
        "beta_eastness": 0.35,
        "beta_season": 0.30,
    }
    assert fixture.generating_theta_obs == {
        "presence_opportunistic": {"gamma_presence_season": 0.35},
    }

    anchors = v04_r2_presence_refusal_anchors(fixture)
    assert len(anchors) == 3
    assert anchors[0][0]["sp"]["beta_season"] == 0.30
    assert anchors[0][1]["presence_opportunistic"]["gamma_presence_season"] == 0.35
    assert anchors[1][0]["sp"]["beta_season"] == 0.55
    assert anchors[1][1]["presence_opportunistic"]["gamma_presence_season"] == 0.10
    assert anchors[2][0]["sp"]["beta_season"] == 0.10
    assert anchors[2][1]["presence_opportunistic"]["gamma_presence_season"] == 0.60


def test_r2_activity_detection_refusal_is_intercept_only_without_calibrated_annotations():
    from esdm.validate.v04_state_activity_r2 import build_v04_r2_fixture

    fixture = build_v04_r2_fixture(
        _sample_csv(),
        profile="activity_detection_refusal",
    )
    activity = next(
        process
        for process in fixture.model.species["sp"]
        if isinstance(process, LinearActivity)
    )

    assert activity.covariates == ()
    assert set(activity.priors()) == {"activity_intercept"}
    assert tuple(stream.name for stream in fixture.model.streams) == (
        "presence_opportunistic",
        "presence_calibrated",
        "annotated_opportunistic",
    )
    assert "activity_beta_diurnal" not in fixture.generating_theta["sp"]
    assert fixture.generating_theta["sp"]["activity_intercept"] == -0.35
    assert fixture.generating_theta_obs["annotated_opportunistic"] == {
        "gamma_annotation_diurnal": 0.30,
        "detection_intercept": 0.40,
    }


def test_r2_positive_and_refusal_anchors_are_frozen():
    from esdm.validate.v04_state_activity_r2 import (
        build_v04_r2_fixture,
        v04_r2_detection_refusal_anchors,
        v04_r2_positive_anchors,
    )

    positive = build_v04_r2_fixture(_sample_csv(), profile="positive")
    anchors = v04_r2_positive_anchors(positive)

    assert len(anchors) == 3
    assert anchors[1][0]["sp"]["beta_season"] == 0.55
    assert anchors[1][1]["presence_opportunistic"]["gamma_presence_season"] == 0.10
    assert anchors[1][0]["sp"]["activity_intercept"] == -0.05
    assert anchors[1][0]["sp"]["activity_beta_diurnal"] == 0.70
    assert anchors[1][1]["annotated_opportunistic"]["gamma_annotation_diurnal"] == 0.10
    assert anchors[1][1]["annotated_opportunistic"]["detection_intercept"] == -0.20
    assert anchors[2][0]["sp"]["beta_foraging_diurnal"] == 0.25
    assert anchors[2][0]["sp"]["beta_foraging_eastness"] == 0.65

    refusal = build_v04_r2_fixture(
        _sample_csv(),
        profile="activity_detection_refusal",
    )
    ranchors = v04_r2_detection_refusal_anchors(refusal)
    assert len(ranchors) == 3
    assert ranchors[0][0]["sp"]["activity_intercept"] == -0.35
    assert ranchors[0][1]["annotated_opportunistic"]["detection_intercept"] == 0.40
    assert ranchors[1][0]["sp"]["activity_intercept"] == 0.20
    assert ranchors[1][1]["annotated_opportunistic"]["detection_intercept"] == -0.30
    assert ranchors[2][0]["sp"]["activity_intercept"] == -0.90
    assert ranchors[2][1]["annotated_opportunistic"]["detection_intercept"] == 0.90
