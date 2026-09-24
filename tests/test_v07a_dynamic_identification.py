import importlib.util

import pytest

from esdm.identify import IdentificationStatus
from esdm.validate.v07a_fixture import V07A_TRUTH, build_v07a_fixture
from esdm.validate.v07a_qualification import evaluate_v07a_identification


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_direct_occupancy_calibration_is_zero_outside_frozen_window():
    fixture = build_v07a_fixture()
    direct = next(
        stream
        for stream in fixture.positive_model.streams
        if stream.name == "occupancy_calibration"
    )
    mask = direct.structural_exposure_mask(fixture.positive_model.domain.keys)

    assert mask[:4] == (True, True, True, True)
    assert not any(mask[4:])


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07a_exact_refusal_and_direct_calibration_gate():
    result = evaluate_v07a_identification()

    assert result.joint_only_refusal_pass
    assert result.positive_structural_pass
    assert result.positive_practical_pass

    for target in V07A_TRUTH:
        assert (
            result.refusal_evidence[target].structural.status
            is IdentificationStatus.NOT_IDENTIFIED
        )
        assert (
            result.positive_evidence[target].structural.status
            is IdentificationStatus.IDENTIFIED
        )
        assert result.positive_evidence[target].practical is not None
        assert result.positive_evidence[target].practical.target_sd_proxy <= 0.25
