import importlib.util

import pytest

from esdm.validate.v07j_confirm import V07J_WORLDS
from esdm.validate.v07k_audit import evaluate_v07k_local_oracle_audit


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07k_audit_evaluates_local_oracle_in_both_shift_worlds():
    audit = evaluate_v07k_local_oracle_audit()

    assert set(audit.worlds) == set(V07J_WORLDS)
    for row in audit.worlds.values():
        assert row.placements_evaluated == 70
        assert len(row.local_oracle_placement) == 4
        assert row.local_oracle_to_transferred_ratio <= 1.0
        assert row.local_oracle_to_baseline_ratio <= 1.0
