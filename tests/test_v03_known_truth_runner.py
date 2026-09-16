import importlib.util
import math

import pytest


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def test_benchmark_summary_aggregates_world_metrics_without_backend():
    from esdm.validate.known_truth import BenchmarkReplicate, summarize_known_truth_benchmark

    records = (
        BenchmarkReplicate(
            world="w",
            replicate=0,
            posterior_mean=0.8,
            interval_low=0.5,
            interval_high=1.1,
            truth=0.6,
            expected_apparent=0.9,
            num_divergences=0,
        ),
        BenchmarkReplicate(
            world="w",
            replicate=1,
            posterior_mean=1.0,
            interval_low=0.7,
            interval_high=1.3,
            truth=0.6,
            expected_apparent=0.9,
            num_divergences=1,
        ),
    )
    summary = summarize_known_truth_benchmark(records)
    row = summary["w"]
    assert row.replicates == 2
    assert math.isclose(row.mean_posterior, 0.9)
    assert math.isclose(row.mean_bias_from_truth, 0.3)
    assert math.isclose(row.mean_bias_from_expected, 0.0, abs_tol=1e-12)
    assert row.truth_coverage == 0.5
    assert row.expected_coverage == 1.0
    assert row.nonzero_rate == 1.0
    assert row.total_divergences == 1


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_known_truth_runner_executes_generic_correct_and_knockout_worlds():
    from esdm.validate.known_truth import run_v03_known_truth_benchmark

    result = run_v03_known_truth_benchmark(
        world_names=("correct_effort", "suitability_knockout"),
        replicates=1,
        base_seed=41,
        num_warmup=80,
        num_samples=100,
        progress_bar=False,
    )

    assert tuple(result.summary) == ("correct_effort", "suitability_knockout")
    assert len(result.replicates) == 2
    correct = result.summary["correct_effort"]
    knockout = result.summary["suitability_knockout"]
    assert correct.mean_posterior > knockout.mean_posterior + 0.2
    assert correct.total_divergences >= 0
    assert knockout.total_divergences >= 0
