import math

import pytest

from esdm.interaction.overlap import geographic_overlap, overlap_coefficient, state_overlap


def test_geographic_overlap_can_be_complete_while_state_overlap_is_zero():
    assert geographic_overlap([0.5, 0.5], [0.5, 0.5]) == pytest.approx(1.0)
    assert state_overlap(
        {"early": 1.0, "late": 0.0},
        {"early": 0.0, "late": 1.0},
    ) == pytest.approx(0.0)


def test_overlap_normalizes_nonnegative_inputs():
    assert overlap_coefficient([1.0, 1.0], [2.0, 2.0]) == pytest.approx(1.0)
    assert overlap_coefficient([1.0, 0.0], [1.0, 1.0]) == pytest.approx(0.5)


@pytest.mark.parametrize(
    "left,right",
    [
        ([0.0, 0.0], [1.0, 0.0]),
        ([-1.0, 2.0], [1.0, 0.0]),
        ([math.inf, 1.0], [1.0, 0.0]),
    ],
)
def test_overlap_rejects_invalid_vectors(left, right):
    with pytest.raises(ValueError):
        overlap_coefficient(left, right)
