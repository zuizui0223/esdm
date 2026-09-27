from esdm.model.backend_numpyro import NumPyroSBCResult
from esdm.validate.v031_sbc_gate import V031SBCGateConfig, evaluate_v031_sbc_gate


def _balanced(draw_count=9, repeats=10):
    ranks = tuple(rank for _ in range(repeats) for rank in range(draw_count + 1))
    counts = tuple(draw_count for _ in ranks)
    ess = tuple(float(draw_count) for _ in ranks)
    return ranks, counts, ess


def _result(*, bad=False, num_chains=2):
    ranks_a, counts_a, ess_a = _balanced()
    ranks_b, counts_b, ess_b = _balanced()
    if bad:
        ranks_b = tuple(0 for _ in ranks_b)
    return NumPyroSBCResult(
        ranks={"ecological.beta": ranks_a, "observation.gamma": ranks_b},
        posterior_draw_count=20,
        replicates=100,
        divergences_by_replicate=tuple(0 for _ in range(100)),
        draw_counts_by_site={"ecological.beta": counts_a, "observation.gamma": counts_b},
        effective_sample_sizes_by_site={"ecological.beta": ess_a, "observation.gamma": ess_b},
        num_chains=num_chains,
    )


def _config():
    return V031SBCGateConfig(
        replicates=100,
        alpha=0.05,
        envelope_simulations=1000,
        evaluation_points=19,
        envelope_seed=20260919,
        required_num_chains=2,
        max_mean_divergences_per_fit=0.10,
    )


def test_v031_sbc_gate_passes_balanced_all_parameter_ecdfs():
    decision = evaluate_v031_sbc_gate(_result(), config=_config())
    assert decision.passed
    assert decision.ecdf.passed
    assert set(decision.ecdf.parameter_max_deviation) == {
        "ecological.beta",
        "observation.gamma",
    }


def test_v031_sbc_gate_fails_if_one_parameter_leaves_familywise_envelope():
    decision = evaluate_v031_sbc_gate(_result(bad=True), config=_config())
    assert not decision.passed
    assert not decision.ecdf.passed


def test_v031_sbc_gate_requires_frozen_chain_count():
    decision = evaluate_v031_sbc_gate(_result(num_chains=1), config=_config())
    assert not decision.passed
    checks = {check.name: check for check in decision.checks}
    assert not checks["sbc_num_chains"].passed
