from types import SimpleNamespace

import pytest


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


def _record(
    replicate,
    *,
    activity_precip_mean,
    activity_precip_interval,
    activity_east_mean,
    activity_east_interval,
    state_precip_mean,
    state_precip_interval,
    state_east_mean,
    state_east_interval,
    full_score,
    activity_knockout_score,
    state_knockout_score,
    divergences,
):
    from esdm.validate.v04_state_activity_run import V04Replicate

    return V04Replicate(
        replicate=replicate,
        activity_beta_precip_mean=activity_precip_mean,
        activity_beta_precip_low=activity_precip_interval[0],
        activity_beta_precip_high=activity_precip_interval[1],
        activity_beta_eastness_mean=activity_east_mean,
        activity_beta_eastness_low=activity_east_interval[0],
        activity_beta_eastness_high=activity_east_interval[1],
        state_beta_precip_mean=state_precip_mean,
        state_beta_precip_low=state_precip_interval[0],
        state_beta_precip_high=state_precip_interval[1],
        state_beta_eastness_mean=state_east_mean,
        state_beta_eastness_low=state_east_interval[0],
        state_beta_eastness_high=state_east_interval[1],
        full_heldout_log_score=full_score,
        activity_knockout_heldout_log_score=activity_knockout_score,
        state_knockout_heldout_log_score=state_knockout_score,
        full_divergences=divergences[0],
        activity_knockout_divergences=divergences[1],
        state_knockout_divergences=divergences[2],
    )


def test_v04_summary_arithmetic_uses_frozen_truth_and_three_fits_per_replicate():
    from esdm.validate.v04_state_activity_run import summarize_v04_state_activity

    rows = (
        _record(
            0,
            activity_precip_mean=0.65,
            activity_precip_interval=(0.50, 0.80),
            activity_east_mean=0.35,
            activity_east_interval=(0.20, 0.55),
            state_precip_mean=-0.45,
            state_precip_interval=(-0.70, -0.30),
            state_east_mean=0.50,
            state_east_interval=(0.30, 0.60),
            full_score=-1.0,
            activity_knockout_score=-1.10,
            state_knockout_score=-1.05,
            divergences=(0, 1, 0),
        ),
        _record(
            1,
            activity_precip_mean=0.50,
            activity_precip_interval=(0.20, 0.40),
            activity_east_mean=0.45,
            activity_east_interval=(0.41, 0.60),
            state_precip_mean=-0.60,
            state_precip_interval=(-0.45, -0.20),
            state_east_mean=0.40,
            state_east_interval=(0.10, 0.30),
            full_score=-1.2,
            activity_knockout_score=-1.15,
            state_knockout_score=-1.30,
            divergences=(1, 0, 0),
        ),
    )
    identification = SimpleNamespace(
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
    )

    summary = summarize_v04_state_activity(
        rows,
        identification=identification,
        extrapolation_integrity=True,
    )

    assert summary.replicates == 2
    assert summary.fit_count == 6
    assert summary.total_divergences == 2
    assert summary.activity_beta_precip_mean_bias == pytest.approx(0.025)
    assert summary.activity_beta_eastness_mean_bias == pytest.approx(0.0)
    assert summary.state_beta_precip_mean_bias == pytest.approx(-0.025)
    assert summary.state_beta_eastness_mean_bias == pytest.approx(0.0)
    assert summary.activity_beta_precip_coverage == 0.5
    assert summary.activity_beta_eastness_coverage == 0.5
    assert summary.state_beta_precip_coverage == 0.5
    assert summary.state_beta_eastness_coverage == 0.5
    assert summary.activity_positive_gain_rate == 0.5
    assert summary.mean_activity_gain == pytest.approx(0.025)
    assert summary.state_positive_gain_rate == 1.0
    assert summary.mean_state_gain == pytest.approx(0.075)


def test_v04_data_subsetting_preserves_nested_state_shape_without_heldout_leakage():
    from esdm.validate.v04_state_activity import build_v04_state_activity_fixture
    from esdm.validate.v04_state_activity_run import _subset_data, _subset_model

    fixture = build_v04_state_activity_fixture(_sample_csv(), profile="positive")
    train_model, _ = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout=None,
    )
    all_keys = fixture.model.domain.keys
    generated_counts = {
        "presence": {
            "sp": {key: 1 for key in all_keys},
        },
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
    assert set(subset["presence"]["sp"]) == train_keys
    assert set(subset["annotated"]["sp"]["resting"]) == train_keys
    assert set(subset["annotated"]["sp"]["foraging"]) == train_keys
    assert not (set(subset["presence"]["sp"]) & heldout_keys)
