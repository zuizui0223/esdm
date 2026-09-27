from types import SimpleNamespace
import math

import pytest


TARGETS = (
    "sp.suitability.beta_precip",
    "stream.opportunistic.gamma_precip",
    "stream.opportunistic.gamma_season",
    "stream.opportunistic.gamma_hour",
    "stream.opportunistic.detection_intercept",
    "sp.activity.activity_beta_precip",
    "sp.activity.activity_beta_eastness",
    "sp.activity.activity_beta_season",
    "sp.activity.activity_beta_hour",
    "sp.state.beta_foraging_precip",
    "sp.state.beta_foraging_eastness",
    "sp.state.beta_foraging_season",
    "sp.state.beta_foraging_hour",
)

TRUTH = {
    "sp.suitability.beta_precip": 0.45,
    "stream.opportunistic.gamma_precip": 0.35,
    "stream.opportunistic.gamma_season": 0.30,
    "stream.opportunistic.gamma_hour": -0.25,
    "stream.opportunistic.detection_intercept": -0.20,
    "sp.activity.activity_beta_precip": 0.50,
    "sp.activity.activity_beta_eastness": 0.35,
    "sp.activity.activity_beta_season": 0.55,
    "sp.activity.activity_beta_hour": 0.40,
    "sp.state.beta_foraging_precip": -0.45,
    "sp.state.beta_foraging_eastness": 0.40,
    "sp.state.beta_foraging_season": 0.50,
    "sp.state.beta_foraging_hour": -0.45,
}


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


def _record(replicate, mean_offset, covers, activity_gain, state_gain, divergences):
    from esdm.validate.v04_r2_run import V04R2Replicate

    means = {target: truth + mean_offset for target, truth in TRUTH.items()}
    lows = {
        target: (truth - 0.1 if covers else truth + 0.2)
        for target, truth in TRUTH.items()
    }
    highs = {
        target: (truth + 0.1 if covers else truth + 0.4)
        for target, truth in TRUTH.items()
    }
    return V04R2Replicate(
        replicate=replicate,
        posterior_means=means,
        posterior_lows=lows,
        posterior_highs=highs,
        full_heldout_log_score=-1.0,
        activity_knockout_heldout_log_score=-1.0 - activity_gain,
        state_knockout_heldout_log_score=-1.0 - state_gain,
        full_divergences=divergences[0],
        activity_knockout_divergences=divergences[1],
        state_knockout_divergences=divergences[2],
    )


def test_r2_summary_arithmetic_uses_all_13_truths_and_three_fits():
    from esdm.validate.v04_r2_run import summarize_v04_r2

    rows = (
        _record(0, 0.10, True, 0.02, 0.03, (0, 1, 0)),
        _record(1, -0.05, False, -0.01, 0.01, (1, 0, 0)),
    )
    identification = SimpleNamespace(
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
    )

    summary = summarize_v04_r2(
        rows,
        identification=identification,
        extrapolation_integrity=True,
    )

    assert summary.replicates == 2
    assert summary.fit_count == 6
    assert summary.total_divergences == 2
    for target in TARGETS:
        assert summary.mean_biases[target] == pytest.approx(0.025)
        assert summary.coverages[target] == 0.5
    assert summary.activity_positive_gain_rate == 0.5
    assert summary.mean_activity_gain == pytest.approx(0.005)
    assert summary.state_positive_gain_rate == 1.0
    assert summary.mean_state_gain == pytest.approx(0.02)


def test_r2_data_subsetting_preserves_three_stream_shapes_and_excludes_east():
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture
    from esdm.validate.v04_r2_run import _subset_data, _subset_model

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    train_model, _ = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout=None,
    )
    all_keys = fixture.model.domain.keys
    generated_counts = {
        "opportunistic": {"sp": {key: 1 for key in all_keys}},
        "calibrated": {"sp": {key: 0 for key in all_keys}},
        "annotated": {
            "sp": {
                "resting": {key: 0 for key in all_keys},
                "foraging": {key: 0 for key in all_keys},
            }
        },
    }

    subset = _subset_data(generated_counts, train_model)
    train_keys = set(train_model.domain.keys)
    heldout_keys = {
        key for key in all_keys if key[0] in set(fixture.heldout_spaces)
    }

    assert set(subset["opportunistic"]["sp"]) == train_keys
    assert set(subset["calibrated"]["sp"]) == train_keys
    assert set(subset["annotated"]["sp"]["resting"]) == train_keys
    assert set(subset["annotated"]["sp"]["foraging"]) == train_keys
    assert not (set(subset["opportunistic"]["sp"]) & heldout_keys)


def _poisson_log_mass(count, rate):
    if rate == 0.0:
        return 0.0 if count == 0 else -math.inf
    return count * math.log(rate) - rate - math.lgamma(count + 1.0)


def _logmeanexp(values):
    rows = tuple(values)
    maximum = max(rows)
    return maximum + math.log(
        sum(math.exp(value - maximum) for value in rows) / len(rows)
    )


def test_r2_state_score_averages_two_state_blocks_and_all_contexts(monkeypatch):
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture
    from esdm.validate.v04_r2_run import (
        _state_block_log_predictive_density,
        _subset_model,
    )
    from esdm.model import backend_numpyro

    fixture = build_v04_r2_fixture(_sample_csv(), profile="positive")
    heldout, covariates = _subset_model(
        fixture,
        fixture.heldout_spaces[:1],
        knockout=None,
    )
    keys = heldout.domain.keys
    n = len(keys)
    fake = {
        "annotated.sp.resting": (
            tuple(1.0 for _ in keys),
            tuple(2.0 for _ in keys),
        ),
        "annotated.sp.foraging": (
            tuple(0.5 for _ in keys),
            tuple(1.5 for _ in keys),
        ),
    }
    monkeypatch.setattr(
        backend_numpyro,
        "posterior_observation_rates",
        lambda model, samples, covariates: fake,
    )
    data = {
        "annotated": {
            "sp": {
                "resting": {key: 0 for key in keys},
                "foraging": {key: 1 for key in keys},
            }
        }
    }

    observed = _state_block_log_predictive_density(
        heldout,
        samples={},
        covariates=covariates,
        data=data,
    )
    resting = _logmeanexp(
        (_poisson_log_mass(0, 1.0), _poisson_log_mass(0, 2.0))
    )
    foraging = _logmeanexp(
        (_poisson_log_mass(1, 0.5), _poisson_log_mass(1, 1.5))
    )
    expected = (resting + foraging) / 2.0
    assert n > 0
    assert observed == pytest.approx(expected)
