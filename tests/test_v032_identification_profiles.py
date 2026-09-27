import importlib.util

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


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


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_frozen_positive_and_negative_identification_profiles_discriminate():
    from esdm.validate.v032_semisynthetic_gate import evaluate_v032_identification_profiles

    result = evaluate_v032_identification_profiles(_sample_csv())
    assert result.positive_structural_pass is True
    assert result.positive_practical_pass is True
    assert result.negative_structural_pass is True
    assert result.negative_practical_refused is True
    assert len(result.positive_anchor_evidence) == 3
    assert len(result.negative_anchor_evidence) == 3

    for anchor in result.positive_anchor_evidence:
        assert anchor.beta_precip.structural.status.value == "Identified"
        assert anchor.gamma_precip.structural.status.value == "Identified"
        assert anchor.beta_precip.practical is not None
        assert anchor.gamma_precip.practical is not None
        assert anchor.beta_precip.practical.weak is False
        assert anchor.gamma_precip.practical.weak is False

    for anchor in result.negative_anchor_evidence:
        assert anchor.beta_precip.structural.status.value == "Identified"
        assert anchor.gamma_precip.structural.status.value == "Identified"
        assert (
            anchor.beta_precip.practical.weak
            or anchor.gamma_precip.practical.weak
        )
