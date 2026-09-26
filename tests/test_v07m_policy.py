from __future__ import annotations

import importlib.util
import math

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None

from esdm.validate.v07l_fixture import V07L_WORLD_PROBABILITIES
from esdm.validate.v07m_policy import (
    V07M_ABSOLUTE_SD_THRESHOLD,
    V07M_EXPECTED_ACTIONS,
    V07M_RELATIVE_HEADROOM_THRESHOLD,
    decide_v07m_from_scores,
    frozen_v07m_role_cells,
)


def _decision(a, t):
    return decide_v07m_from_scores(
        adaptive_placement=(1, 2, 7, 8),
        adaptive_worst_dynamic_sd=a,
        transferred_worst_dynamic_sd=t,
    )


def test_v07m_policy_uses_preexisting_absolute_and_relative_thresholds():
    assert V07M_ABSOLUTE_SD_THRESHOLD == 0.35
    assert V07M_RELATIVE_HEADROOM_THRESHOLD == 0.80

    assert _decision(0.36, 0.50).action == "abstain"
    assert _decision(0.34, 0.36).action == "adaptive"
    assert _decision(0.24, 0.32).action == "adaptive"
    assert _decision(0.31, 0.33).action == "transferred"


def test_v07m_absolute_adequacy_precedes_relative_headroom():
    result = _decision(0.36, 0.60)

    assert result.adaptive_to_transferred_ratio == 0.6
    assert result.action == "abstain"
    assert result.reason == "no_placement_meets_absolute_precision"


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07m_fresh_roles_are_deterministically_disjoint_from_v07l_worlds():
    roles = frozen_v07m_role_cells()

    assert set(roles) == set(V07M_EXPECTED_ACTIONS)
    old_worlds = {
        (
            row["psi0"],
            row["gamma"],
            row["epsilon"],
        )
        for row in V07L_WORLD_PROBABILITIES.values()
    }
    new_worlds = {
        (
            row["cell"].psi0,
            row["cell"].gamma,
            row["cell"].epsilon,
        )
        for row in roles.values()
    }

    assert old_worlds.isdisjoint(new_worlds)
    for role, row in roles.items():
        assert row["decision"].action == V07M_EXPECTED_ACTIONS[role]


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07m_frozen_role_geometry_matches_contract_numbers():
    roles = frozen_v07m_role_cells()

    expected = {
        "adaptive_large_headroom": (
            0.2472385696777683,
            0.3646050116562837,
            0.6780997566507458,
        ),
        "adaptive_absolute_rescue": (
            0.33916535312516777,
            0.35202920272273763,
            0.9634580043414706,
        ),
        "transfer_adequate": (
            0.31342660399042044,
            0.3309299120235847,
            0.9471087157817368,
        ),
        "abstain_inadequate": (
            0.42356213088384326,
            0.46239800754752164,
            0.9160120155585075,
        ),
    }
    for role, (a, t, ratio) in expected.items():
        decision = roles[role]["decision"]
        assert math.isclose(
            decision.adaptive_worst_dynamic_sd, a, rel_tol=0.0, abs_tol=1e-12
        )
        assert math.isclose(
            decision.transferred_worst_dynamic_sd, t, rel_tol=0.0, abs_tol=1e-12
        )
        assert math.isclose(
            decision.adaptive_to_transferred_ratio,
            ratio,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
