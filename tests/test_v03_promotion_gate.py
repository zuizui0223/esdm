from esdm.validate.known_truth import BenchmarkSummary


def _summary(
    world,
    *,
    replicates=100,
    mean_posterior=0.0,
    mean_bias_from_truth=0.0,
    mean_bias_from_expected=0.0,
    truth_coverage=0.9,
    expected_coverage=0.9,
    nonzero_rate=0.0,
    total_divergences=0,
):
    return BenchmarkSummary(
        world=world,
        replicates=replicates,
        mean_posterior=mean_posterior,
        mean_bias_from_truth=mean_bias_from_truth,
        mean_bias_from_expected=mean_bias_from_expected,
        truth_coverage=truth_coverage,
        expected_coverage=expected_coverage,
        nonzero_rate=nonzero_rate,
        total_divergences=total_divergences,
    )


def test_frozen_promotion_gate_passes_declared_good_and_negative_controls():
    from esdm.validate.known_truth import evaluate_v03_promotion_gate

    summaries = {
        "correct_effort": _summary(
            "correct_effort",
            mean_posterior=0.63,
            mean_bias_from_truth=0.03,
            mean_bias_from_expected=0.03,
            truth_coverage=0.90,
            nonzero_rate=0.92,
            total_divergences=2,
        ),
        "suitability_knockout": _summary(
            "suitability_knockout",
            mean_posterior=0.04,
            mean_bias_from_truth=0.04,
            mean_bias_from_expected=0.04,
            truth_coverage=0.91,
            nonzero_rate=0.08,
            total_divergences=0,
        ),
        "wrong_effort_geometry": _summary(
            "wrong_effort_geometry",
            mean_posterior=1.22,
            mean_bias_from_truth=0.62,
            mean_bias_from_expected=-0.08,
            truth_coverage=0.05,
            expected_coverage=0.90,
            nonzero_rate=1.0,
            total_divergences=1,
        ),
        "hidden_driver": _summary(
            "hidden_driver",
            mean_posterior=0.95,
            mean_bias_from_truth=0.55,
            mean_bias_from_expected=-0.05,
            truth_coverage=0.08,
            expected_coverage=0.88,
            nonzero_rate=1.0,
            total_divergences=1,
        ),
    }
    decision = evaluate_v03_promotion_gate(summaries)
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_gate_fails_if_misspecification_does_not_show_predeclared_bias():
    from esdm.validate.known_truth import evaluate_v03_promotion_gate

    summaries = {
        "correct_effort": _summary(
            "correct_effort", mean_posterior=0.6, nonzero_rate=0.9
        ),
        "suitability_knockout": _summary("suitability_knockout"),
        "wrong_effort_geometry": _summary(
            "wrong_effort_geometry",
            mean_posterior=0.65,
            mean_bias_from_truth=0.05,
            mean_bias_from_expected=-0.65,
            nonzero_rate=1.0,
        ),
        "hidden_driver": _summary(
            "hidden_driver",
            mean_posterior=0.95,
            mean_bias_from_truth=0.55,
            mean_bias_from_expected=-0.05,
            nonzero_rate=1.0,
        ),
    }
    decision = evaluate_v03_promotion_gate(summaries)
    assert decision.passed is False
    failed = {check.name for check in decision.checks if not check.passed}
    assert "wrong_effort_negative_control" in failed


def test_gate_requires_frozen_replicate_count_by_default():
    from esdm.validate.known_truth import evaluate_v03_promotion_gate

    summaries = {
        "correct_effort": _summary("correct_effort", replicates=99, mean_posterior=0.6, nonzero_rate=0.9),
        "suitability_knockout": _summary("suitability_knockout"),
        "wrong_effort_geometry": _summary("wrong_effort_geometry", mean_posterior=1.3, mean_bias_from_truth=0.7, mean_bias_from_expected=0.0),
        "hidden_driver": _summary("hidden_driver", mean_posterior=1.0, mean_bias_from_truth=0.6, mean_bias_from_expected=0.0),
    }
    decision = evaluate_v03_promotion_gate(summaries)
    assert decision.passed is False
    assert any(check.name == "correct_effort_replicates" and not check.passed for check in decision.checks)
