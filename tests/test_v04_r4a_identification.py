import importlib.util
import os

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None
R4A_OUTCOME_ENABLED = os.environ.get("ESDM_RUN_R4A_QUALIFICATION") == "1"


def _sample_csv(rows=130):
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(rows):
        latitude = 22.0 + (i % 31) * 0.75
        longitude = -154.0 + (i % 43) * 2.25
        average = 45.0 + ((i * 7) % 29) * 1.3
        total19 = 35.0 + (i % 13) * 1.7
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.3f},"
            f"{latitude:.4f},{longitude:.4f},ST,{total19:.1f}"
        )
    return "\n".join(lines) + "\n"


@pytest.mark.skipif(
    not JAX_AVAILABLE or not R4A_OUTCOME_ENABLED,
    reason="R4a outcome test requires explicit authorization environment",
)
def test_r4a_evaluator_returns_frozen_evidence_shape():
    from esdm.validate.v04_r2_gate import R2_IDENTIFICATION_TARGETS
    from esdm.validate.v04_r4a_gate import evaluate_v04_r4a_identification

    result = evaluate_v04_r4a_identification(_sample_csv())

    assert len(R2_IDENTIFICATION_TARGETS) == 13
    assert len(result.positive_anchor_evidence) == 3
    assert all(len(anchor) == 13 for anchor in result.positive_anchor_evidence)
    assert len(result.sparse_anchor_evidence) == 3
    assert all(len(anchor) == 13 for anchor in result.sparse_anchor_evidence)
    assert len(result.unknown_anchor_evidence) == 3
    assert all(len(anchor) == 2 for anchor in result.unknown_anchor_evidence)
