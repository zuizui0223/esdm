import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07G_FRONTIER_SELECTION.json"
        ).read_text(encoding="utf-8")
    )


def test_v07g_selection_is_frozen_before_mcmc():
    payload = _payload()

    assert payload["status"] == "FROZEN_SELECTION"
    assert payload["selection_run_id"] == 36105062429
    assert payload["placements_evaluated"] == 70
    assert payload["eligible_placements"] == 70
    assert payload["selected"]["placement"] == [2, 6, 7, 8]
    assert payload["baseline"]["placement"] == [1, 2, 3, 4]
    assert payload["selected_to_baseline_worst_sd_ratio"] < 0.69
    assert payload["total_direct_effort_per_design"] == 2000.0
    assert payload["artifact"]["github_digest"] == (
        "sha256:45d19db95b45f03c0144a9e11e5636edd3387ff1c8e393eaefbbe0478356eae5"
    )
