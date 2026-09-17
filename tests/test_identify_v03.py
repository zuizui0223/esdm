import pytest

from esdm.identify import (
    IdentificationStatus,
    contraction_diagnostic,
    identify_from_contraction,
    sbc_rank_histogram,
)


def test_contraction_reports_ratio_and_identification_boundary():
    diag = contraction_diagnostic(prior_sd=2.0, posterior_samples=(0.9, 1.0, 1.1, 1.0))
    assert diag.posterior_sd < diag.prior_sd
    assert 0.0 <= diag.contraction_fraction <= 1.0
    result = identify_from_contraction(diag, minimum_contraction=0.5, target="beta")
    assert result.status is IdentificationStatus.IDENTIFIED

    weak = contraction_diagnostic(prior_sd=1.0, posterior_samples=(-0.9, 0.9, -0.8, 0.8))
    result = identify_from_contraction(weak, minimum_contraction=0.5, target="beta")
    assert result.status is IdentificationStatus.NOT_IDENTIFIED


def test_sbc_rank_histogram_distinguishes_calibration_from_misspecification():
    balanced = sbc_rank_histogram(
        ranks=(0, 1, 2, 3, 0, 1, 2, 3),
        posterior_draw_count=3,
        bins=4,
        max_total_variation=0.01,
    )
    assert balanced.calibrated

    skewed = sbc_rank_histogram(
        ranks=(0, 0, 0, 0, 0, 1, 0, 0),
        posterior_draw_count=3,
        bins=4,
        max_total_variation=0.2,
    )
    assert not skewed.calibrated


def test_invalid_rank_is_rejected():
    with pytest.raises(ValueError):
        sbc_rank_histogram(ranks=(4,), posterior_draw_count=3, bins=4)
