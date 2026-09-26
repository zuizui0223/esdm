from __future__ import annotations

import pytest

from esdm.validate.v07l_fixture import (
    V07L_AUDIT_ORACLE_PLACEMENTS,
    V07L_AUDIT_ORACLE_RATIOS,
    V07L_TRIGGER_RATIO,
    V07L_TRANSFERRED_PLACEMENT,
    V07L_WORLD_PROBABILITIES,
    V07L_WORLDS,
    theta_for_v07l_world,
)


def test_v07l_worlds_and_trigger_match_frozen_audit():
    assert V07L_TRIGGER_RATIO == 0.80
    assert V07L_WORLDS == (
        "strong_headroom",
        "threshold_below",
        "threshold_above",
        "negligible_headroom",
    )
    assert V07L_AUDIT_ORACLE_RATIOS == {
        "strong_headroom": pytest.approx(0.6737454617843512),
        "threshold_below": pytest.approx(0.7450786540043693),
        "threshold_above": pytest.approx(0.8692745421491),
        "negligible_headroom": pytest.approx(1.0),
    }
    assert V07L_AUDIT_ORACLE_RATIOS["strong_headroom"] < V07L_TRIGGER_RATIO
    assert V07L_AUDIT_ORACLE_RATIOS["threshold_below"] < V07L_TRIGGER_RATIO
    assert V07L_AUDIT_ORACLE_RATIOS["threshold_above"] > V07L_TRIGGER_RATIO
    assert V07L_AUDIT_ORACLE_RATIOS["negligible_headroom"] > V07L_TRIGGER_RATIO


def test_v07l_selected_oracles_are_exactly_frozen():
    assert V07L_AUDIT_ORACLE_PLACEMENTS == {
        "strong_headroom": (1, 2, 7, 8),
        "threshold_below": (1, 2, 3, 8),
        "threshold_above": (1, 3, 4, 8),
        "negligible_headroom": (2, 6, 7, 8),
    }
    assert V07L_TRANSFERRED_PLACEMENT == (2, 6, 7, 8)


def test_v07l_world_probabilities_are_fresh_and_common_psi0():
    assert set(V07L_WORLD_PROBABILITIES) == set(V07L_WORLDS)
    assert all(
        row["psi0"] == pytest.approx(0.85)
        for row in V07L_WORLD_PROBABILITIES.values()
    )
    assert V07L_WORLD_PROBABILITIES["strong_headroom"]["epsilon"] == pytest.approx(0.38)
    assert V07L_WORLD_PROBABILITIES["threshold_above"]["epsilon"] == pytest.approx(0.08)
    assert V07L_WORLD_PROBABILITIES["negligible_headroom"]["gamma"] == pytest.approx(0.65)


def test_v07l_theta_conversion_is_finite_for_all_worlds():
    for world in V07L_WORLDS:
        theta = theta_for_v07l_world(world)["sp"]
        assert theta["alpha"] == pytest.approx(0.30)
        assert all(
            value == pytest.approx(value)
            for value in theta.values()
        )
