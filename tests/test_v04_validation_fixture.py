from esdm.observe import EffortField, KnownDetection, LogitDetection


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


def test_positive_fixture_matches_frozen_geometry_truth_and_exposure():
    from esdm.validate.v04_state_activity import build_v04_state_activity_fixture

    fixture = build_v04_state_activity_fixture(_sample_csv(), profile="positive")

    assert len(fixture.model.domain.keys) == 120 * 6 * 4
    assert len(fixture.calibration_spaces) == 18
    assert set(fixture.calibration_spaces) < set(fixture.train_spaces)
    assert not (set(fixture.calibration_spaces) & set(fixture.heldout_spaces))

    presence, annotated = fixture.model.streams
    assert isinstance(presence.effort, EffortField)
    assert isinstance(annotated.effort, EffortField)
    assert isinstance(annotated.detection, KnownDetection)
    assert annotated.detection.probability({}) == 0.85

    calibration_key = (fixture.calibration_spaces[0], 15, 0)
    heldout_key = (fixture.heldout_spaces[0], 15, 0)
    uncalibrated = next(
        space
        for space in fixture.train_spaces
        if space not in set(fixture.calibration_spaces)
    )
    uncalibrated_key = (uncalibrated, 15, 0)
    assert presence.effort.at(calibration_key) == 5.0
    assert annotated.effort.at(calibration_key) == 8.0
    assert annotated.effort.at(heldout_key) == 8.0
    assert annotated.effort.at(uncalibrated_key) == 0.0

    assert fixture.generating_theta["sp"] == {
        "intercept": -2.0,
        "beta_precip": 0.45,
        "beta_lat": -0.20,
        "beta_eastness": 0.35,
        "activity_intercept": -0.35,
        "activity_beta_precip": 0.55,
        "activity_beta_eastness": 0.40,
        "alpha_foraging": 0.20,
        "beta_foraging_precip": -0.50,
        "beta_foraging_eastness": 0.45,
    }
    assert fixture.generating_theta_obs == {
        "presence": {},
        "annotated": {},
    }

    train_eastness = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.train_spaces
    ]
    heldout_eastness = [
        fixture.covariates[(space, 15, 0)]["eastness_z_train"]
        for space in fixture.heldout_spaces
    ]
    assert min(heldout_eastness) > max(train_eastness)


def test_sparse_profile_changes_only_training_annotation_geometry():
    from esdm.validate.v04_state_activity import build_v04_state_activity_fixture

    text = _sample_csv()
    positive = build_v04_state_activity_fixture(text, profile="positive")
    sparse = build_v04_state_activity_fixture(text, profile="sparse")

    assert len(sparse.calibration_spaces) == 6
    assert positive.train_spaces == sparse.train_spaces
    assert positive.heldout_spaces == sparse.heldout_spaces
    assert positive.covariates == sparse.covariates
    assert positive.generating_theta == sparse.generating_theta
    assert positive.generating_theta_obs == sparse.generating_theta_obs

    scored = []
    for space in sparse.train_spaces:
        values = sparse.covariates[(space, 15, 0)]
        scored.append(
            (
                values["precip_z_train"] ** 2
                + values["eastness_z_train"] ** 2,
                space,
            )
        )
    expected = tuple(space for _, space in sorted(scored)[:6])
    assert sparse.calibration_spaces == expected


def test_positive_identification_anchors_are_frozen():
    from esdm.validate.v04_state_activity import (
        build_v04_state_activity_fixture,
        v04_identification_anchors,
    )

    fixture = build_v04_state_activity_fixture(_sample_csv(), profile="positive")
    anchors = v04_identification_anchors(fixture)

    assert len(anchors) == 3
    truth = anchors[0][0]["sp"]
    assert truth["activity_beta_precip"] == 0.55
    assert truth["beta_foraging_eastness"] == 0.45

    anchor_b = anchors[1][0]["sp"]
    assert anchor_b["activity_intercept"] == -0.10
    assert anchor_b["activity_beta_precip"] == 0.75
    assert anchor_b["activity_beta_eastness"] == 0.20
    assert anchor_b["alpha_foraging"] == -0.10
    assert anchor_b["beta_foraging_precip"] == -0.25
    assert anchor_b["beta_foraging_eastness"] == 0.70

    anchor_c = anchors[2][0]["sp"]
    assert anchor_c["activity_intercept"] == -0.70
    assert anchor_c["activity_beta_precip"] == 0.30
    assert anchor_c["activity_beta_eastness"] == 0.65
    assert anchor_c["alpha_foraging"] == 0.50
    assert anchor_c["beta_foraging_precip"] == -0.75
    assert anchor_c["beta_foraging_eastness"] == 0.20


def test_unknown_detection_fixture_is_intercept_only_and_frozen():
    from esdm.validate.v04_state_activity import (
        build_v04_unknown_detection_fixture,
        v04_unknown_detection_anchors,
    )

    fixture = build_v04_unknown_detection_fixture(_sample_csv())
    activity = fixture.model.species["sp"][1]
    annotated = fixture.model.streams[1]

    assert activity.covariates == ()
    assert set(activity.priors()) == {"activity_intercept"}
    assert isinstance(annotated.detection, LogitDetection)
    assert fixture.generating_theta["sp"]["activity_intercept"] == -0.35
    assert "activity_beta_precip" not in fixture.generating_theta["sp"]
    assert fixture.generating_theta_obs["annotated"] == {
        "detection_intercept": 0.40
    }
    assert len(fixture.calibration_spaces) == 18

    anchors = v04_unknown_detection_anchors(fixture)
    assert len(anchors) == 3
    assert anchors[0][0]["sp"]["activity_intercept"] == -0.35
    assert anchors[0][1]["annotated"]["detection_intercept"] == 0.40
    assert anchors[1][0]["sp"]["activity_intercept"] == 0.20
    assert anchors[1][1]["annotated"]["detection_intercept"] == -0.30
    assert anchors[2][0]["sp"]["activity_intercept"] == -0.90
    assert anchors[2][1]["annotated"]["detection_intercept"] == 0.90
