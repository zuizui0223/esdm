from esdm.observe import EffortField, LogLinearEffort


def _sample_csv(rows=130):
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(rows):
        # Deterministic geometry crossing all frozen longitude blocks.
        latitude = 22.0 + (i % 31) * 0.75
        longitude = -154.0 + (i % 43) * 2.25
        average = 45.0 + ((i * 7) % 29) * 1.3
        total19 = 35.0 + (i % 13) * 1.7
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.3f},{latitude:.4f},{longitude:.4f},ST,{total19:.1f}"
        )
    return "\n".join(lines) + "\n"


def test_v032_fixture_has_unknown_effort_partial_calibration_and_true_extrapolation():
    from esdm.validate.v032_semisynthetic import build_v032_semisynthetic_fixture

    fixture = build_v032_semisynthetic_fixture(_sample_csv(), profile="positive")
    assert len(fixture.model.domain.keys) == 120 * 6 * 4
    assert fixture.profile == "positive"
    assert len(fixture.calibration_spaces) == 12
    assert set(fixture.calibration_spaces) < set(fixture.train_spaces)
    assert not (set(fixture.calibration_spaces) & set(fixture.heldout_spaces))

    opportunistic, calibrated = fixture.model.streams
    assert isinstance(opportunistic.effort, LogLinearEffort)
    assert opportunistic.effort.coefficient_parameter == "gamma_precip"
    assert isinstance(calibrated.effort, EffortField)
    assert calibrated.effort.at((fixture.heldout_spaces[0], 15, 0)) == 0.0
    assert calibrated.effort.at((fixture.calibration_spaces[0], 15, 0)) == 3.0

    train_eastness = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.train_spaces
    ]
    heldout_eastness = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.heldout_spaces
    ]
    assert min(heldout_eastness) > max(train_eastness)

    assert fixture.generating_theta["sp"] == {
        "intercept": -2.0,
        "beta_precip": 0.45,
        "beta_lat": -0.20,
        "beta_eastness": 0.35,
    }
    assert fixture.generating_theta_obs["opportunistic"] == {"gamma_precip": 0.40}


def test_positive_and_negative_profiles_change_only_calibration_geometry():
    from esdm.validate.v032_semisynthetic import build_v032_semisynthetic_fixture

    text = _sample_csv()
    positive = build_v032_semisynthetic_fixture(text, profile="positive")
    negative = build_v032_semisynthetic_fixture(text, profile="negative")

    assert len(positive.calibration_spaces) == 12
    assert len(negative.calibration_spaces) == 1
    assert positive.train_spaces == negative.train_spaces
    assert positive.heldout_spaces == negative.heldout_spaces
    assert positive.covariates == negative.covariates
    assert positive.generating_theta == negative.generating_theta
    assert positive.generating_theta_obs == negative.generating_theta_obs

    negative_space = negative.calibration_spaces[0]
    negative_abs_precip = abs(
        negative.covariates[(negative_space, 15, 0)]["precip_z_train"]
    )
    assert negative_abs_precip == min(
        abs(negative.covariates[(space, 15, 0)]["precip_z_train"])
        for space in negative.train_spaces
    )


def test_v032_identification_anchors_are_frozen_and_outcome_independent():
    from esdm.validate.v032_semisynthetic import (
        build_v032_semisynthetic_fixture,
        v032_identification_anchors,
    )

    fixture = build_v032_semisynthetic_fixture(_sample_csv(), profile="positive")
    anchors = v032_identification_anchors(fixture)
    assert len(anchors) == 3
    assert anchors[0][0]["sp"]["beta_precip"] == 0.45
    assert anchors[0][1]["opportunistic"]["gamma_precip"] == 0.40
    assert anchors[1][0]["sp"]["intercept"] == -1.7
    assert anchors[1][0]["sp"]["beta_precip"] == 0.70
    assert anchors[1][1]["opportunistic"]["gamma_precip"] == 0.15
    assert anchors[2][0]["sp"]["intercept"] == -2.3
    assert anchors[2][0]["sp"]["beta_precip"] == 0.20
    assert anchors[2][1]["opportunistic"]["gamma_precip"] == 0.65
