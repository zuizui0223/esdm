def test_reduce_v03_fit_results_keeps_claim_restraint_separate():
    from esdm.validate.benchmark import reduce_v03_fit_results

    evidence = reduce_v03_fit_results(
        sbc_total_variation=0.07,
        correct_parameter_draws={"alpha": (0.0, 0.1), "beta": (0.75, 0.85)},
        knockout_parameter_draws={"beta": (-0.04, 0.02, 0.05)},
        wrong_effort_parameter_draws={"alpha": (0.45, 0.55)},
        hidden_driver_parameter_draws={"beta": (0.95, 1.05)},
        hidden_driver_target=0.5,
        restrained_under_misspecification=True,
    )

    assert abs(evidence.knockout_abs_effect - (0.04 + 0.02 + 0.05) / 3) < 1e-12
    assert abs(evidence.wrong_effort_abs_bias - 0.45) < 1e-12
    assert abs(evidence.hidden_driver_abs_bias - 0.5) < 1e-12
    assert evidence.restrained_under_misspecification is True


def test_reduce_v03_fit_results_requires_claim_restraint_explicitly():
    from esdm.validate.benchmark import reduce_v03_fit_results

    try:
        reduce_v03_fit_results(
            sbc_total_variation=0.1,
            correct_parameter_draws={"alpha": (0.0,)},
            knockout_parameter_draws={"beta": (0.0,)},
            wrong_effort_parameter_draws={"alpha": (0.3,)},
            hidden_driver_parameter_draws={"beta": (0.7,)},
            hidden_driver_target=0.5,
            restrained_under_misspecification=None,
        )
    except ValueError as exc:
        assert "claim restraint" in str(exc)
    else:
        raise AssertionError("claim restraint must not be inferred from posterior bias")
