from types import MappingProxyType


def _uniformish_ranks():
    values = []
    for bin_index in range(10):
        values.extend([15 + 30 * bin_index] * 10)
    return tuple(values)


def test_v03_sbc_gate_passes_frozen_profile_with_uniform_target_ranks():
    from esdm.model.backend_numpyro import NumPyroSBCResult
    from esdm.validate.known_truth import evaluate_v03_sbc_gate

    result = NumPyroSBCResult(
        ranks=MappingProxyType({
            "sp.suitability.intercept": _uniformish_ranks(),
            "sp.suitability.beta_x": _uniformish_ranks(),
        }),
        posterior_draw_count=300,
        replicates=100,
        divergences_by_replicate=(0,) * 100,
    )
    decision = evaluate_v03_sbc_gate(result)
    assert decision.passed is True
    assert decision.target == "sp.suitability.beta_x"
    assert decision.histogram.calibrated is True
    assert decision.histogram.total_variation <= 0.20
    assert decision.mean_divergences == 0.0


def test_v03_sbc_gate_fails_wrong_replicate_count_or_rank_shape():
    from esdm.model.backend_numpyro import NumPyroSBCResult
    from esdm.validate.known_truth import evaluate_v03_sbc_gate

    result = NumPyroSBCResult(
        ranks={"sp.suitability.beta_x": (0,) * 99},
        posterior_draw_count=300,
        replicates=99,
        divergences_by_replicate=(0,) * 99,
    )
    decision = evaluate_v03_sbc_gate(result)
    assert decision.passed is False
    failed = {check.name for check in decision.checks if not check.passed}
    assert "sbc_replicates" in failed
    assert "sbc_rank_uniformity" in failed


def test_v03_sbc_gate_fails_excess_divergences():
    from esdm.model.backend_numpyro import NumPyroSBCResult
    from esdm.validate.known_truth import evaluate_v03_sbc_gate

    result = NumPyroSBCResult(
        ranks={"sp.suitability.beta_x": _uniformish_ranks()},
        posterior_draw_count=300,
        replicates=100,
        divergences_by_replicate=(1,) * 20 + (0,) * 80,
    )
    decision = evaluate_v03_sbc_gate(result)
    assert decision.passed is False
    assert any(check.name == "sbc_divergences" and not check.passed for check in decision.checks)
