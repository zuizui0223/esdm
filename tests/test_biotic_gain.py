import math

import pytest

from esdm.interaction.biotic_gain import biotic_information_gain


def test_biotic_information_gain_is_zero_for_identical_scores():
    assert biotic_information_gain([-0.5, -1.0], [-0.5, -1.0]) == pytest.approx(0.0)


def test_biotic_information_gain_is_positive_for_improved_heldout_scores():
    assert biotic_information_gain([-1.0, -1.0], [-0.5, -0.75]) > 0.0


def test_biotic_information_gain_is_negative_for_degraded_heldout_scores():
    assert biotic_information_gain([-0.5, -0.75], [-1.0, -1.0]) < 0.0


def test_biotic_information_gain_respects_row_weights():
    value = biotic_information_gain(
        [-1.0, -1.0],
        [-0.5, -0.9],
        weights=[0.75, 0.25],
    )
    assert value == pytest.approx(0.4)


@pytest.mark.parametrize(
    "without,with_biotic,weights",
    [
        ([-1.0], [-1.0, -0.5], None),
        ([-1.0, math.inf], [-1.0, -0.5], None),
        ([-1.0, -1.0], [-1.0, -0.5], [1.0]),
        ([-1.0, -1.0], [-1.0, -0.5], [1.0, -1.0]),
    ],
)
def test_biotic_information_gain_rejects_invalid_inputs(without, with_biotic, weights):
    with pytest.raises(ValueError):
        biotic_information_gain(without, with_biotic, weights=weights)
