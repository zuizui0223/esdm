def test_v06b_audit_reuses_frozen_v06a_truth_and_removes_direct_stream():
    from esdm.validate.v06a_fixture import V06A_RECOVERY_TRUTH
    from esdm.validate.v06b_joint_audit import _v06a_training_joint_only

    model, _covariates, theta, theta_obs = _v06a_training_joint_only()

    assert tuple(stream.name for stream in model.streams) == ("joint",)
    assert theta_obs == {"joint": {}}
    assert theta["sp"]["suitability_intercept"] == V06A_RECOVERY_TRUTH[
        "sp.suitability.suitability_intercept"
    ]
    assert theta["sp"]["beta_habitat"] == V06A_RECOVERY_TRUTH[
        "sp.suitability.beta_habitat"
    ]
    assert theta["sp"]["access_intercept"] == V06A_RECOVERY_TRUTH[
        "sp.accessibility.access_intercept"
    ]
    assert theta["sp"]["beta_distance"] == V06A_RECOVERY_TRUTH[
        "sp.accessibility.beta_distance"
    ]
