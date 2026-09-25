from __future__ import annotations

import json
from pathlib import Path

from esdm.validate.v07k_fixture import (
    V07K_WORLD_PROBABILITIES,
    V07K_WORLDS,
)


ROOT = Path(__file__).resolve().parents[1]
V07J_RESULT = ROOT / "docs" / "validation" / "V07J_FROZEN_RESULTS.json"
V07J_SURFACE = ROOT / "docs" / "validation" / "V07J_SURFACE_RESULTS.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v07k_parent_v07j_is_successful_robust_transfer_not_failed_gate():
    result = _read(V07J_RESULT)

    assert result["status"] == "PASS"
    assert result["source_schedule"] == [2, 6, 7, 8]
    assert result["summary"]["total_replicates"] == 36
    assert result["summary"]["pooled_selected_lower_worst_sd_rate"] == (
        35 / 36
    )
    assert result["summary"]["pooled_mean_worst_sd_ratio"] == (
        0.7991896040628926
    )
    assert result["summary"]["total_divergences"] == 0
    assert result["gate"] == {
        "passed": True,
        "checks_passed": 36,
        "checks_total": 36,
    }


def test_v07k_stress_worlds_come_from_surface_not_v07j_confirmatory_worlds():
    surface = _read(V07J_SURFACE)

    assert surface["status"] == "COMPLETE"
    assert surface["summary"]["eligible_count"] == 35
    assert surface["summary"]["selected_better_count"] == 30

    positive = surface["transfer_positive_stress"]
    reversal = surface["reversal_stress"]
    assert (positive["psi0"], positive["gamma"], positive["epsilon"]) == (
        0.20,
        0.15,
        0.05,
    )
    assert (reversal["psi0"], reversal["gamma"], reversal["epsilon"]) == (
        0.80,
        0.15,
        0.30,
    )

    assert V07K_WORLDS == ("transfer_positive", "reversal")
    assert V07K_WORLD_PROBABILITIES["transfer_positive"] == {
        "alpha": 0.30,
        "psi0": 0.20,
        "gamma": 0.15,
        "epsilon": 0.05,
    }
    assert V07K_WORLD_PROBABILITIES["reversal"] == {
        "alpha": 0.30,
        "psi0": 0.80,
        "gamma": 0.15,
        "epsilon": 0.30,
    }

    confirmatory = _read(V07J_RESULT)["target_worlds"]
    assert set(confirmatory) == {
        "low_occupancy",
        "high_occupancy",
        "high_turnover",
    }
    assert "transfer_positive" not in confirmatory
    assert "reversal" not in confirmatory
