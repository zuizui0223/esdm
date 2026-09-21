import importlib.util

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


@pytest.fixture
def sample_csv():
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(130):
        latitude = 22.0 + (i % 31) * 0.75
        longitude = -154.0 + (i % 43) * 2.25
        average = 45.0 + ((i * 7) % 29) * 1.3
        total19 = 35.0 + (i % 13) * 1.7
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.3f},{latitude:.4f},{longitude:.4f},ST,{total19:.1f}"
        )
    return "\n".join(lines) + "\n"


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_r2_identification_profiles_separate_all_layers(sample_csv):
    from esdm.validate.v04_r2_gate import (
        R2_IDENTIFICATION_TARGETS,
        evaluate_v04_r2_identification_profiles,
    )

    result = evaluate_v04_r2_identification_profiles(sample_csv)

    assert len(R2_IDENTIFICATION_TARGETS) == 13
    assert result.positive_structural_pass is True
    assert result.positive_practical_pass is True
    assert result.sparse_structural_pass is True
    assert result.sparse_practical_refused is True
    assert result.unknown_detection_refused is True
    assert len(result.positive_anchor_evidence) == 3
    assert len(result.sparse_anchor_evidence) == 3
    assert len(result.unknown_anchor_evidence) == 3

    for anchor in result.positive_anchor_evidence:
        assert len(anchor) == 13
        assert all(row.structural.status.value == "Identified" for row in anchor)
        assert all(
            row.practical is not None and not row.practical.weak
            for row in anchor
        )

    for anchor in result.sparse_anchor_evidence:
        assert len(anchor) == 13
        assert all(row.structural.status.value == "Identified" for row in anchor)
        assert any(
            row.practical is not None and row.practical.weak
            for row in anchor
        )

    for anchor in result.unknown_anchor_evidence:
        assert len(anchor) == 2
        assert all(
            row.structural.status.value == "NotIdentified"
            for row in anchor
        )
        assert all(row.practical is None for row in anchor)
