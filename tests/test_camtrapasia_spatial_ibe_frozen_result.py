"""Receipt-only regression checks for the one-shot CamTrapAsia C1 field result.

Do not download/reopen wildlife source or tune any frozen C1 selection rule.
These tests guarantee that the archived negative heldout result is not silently
promoted to a positive environment or process-model claim.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

RESULT = Path(__file__).resolve().parents[1] / "docs/replication/CAMTRAPASIA_SPATIAL_IBE_FROZEN_RESULT.json"
EXPECTED_SHA256 = "64d02cf51e52d53046baa64d7ffb9cb624037a9d16a35e9e732fda2abece0dc1"


def load():
    raw = RESULT.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    return json.loads(raw)


def test_one_shot_source_receipt_exact():
    r = load()
    assert r["schema_version"] == 1
    assert r["source"]["doi"] == "10.5281/zenodo.10780971"
    assert r["status"] == "C1_EVALUATED_NO_INCREMENTAL_PREDICTIVE_EVIDENCE"
    assert r["source"]["file_md5"] == {
        "metadata": "2b50c534737b0c98a93da54128b10a32",
        "captures": "a73975d7626def4012a4e1197497ba87",
        "traits": "59e0748f8aaf59b23b936248f1e63fc9",
    }
    assert all(len(h) == 64 for h in r["source"]["file_sha256"].values())


def test_source_and_landscape_support_are_frozen():
    r = load()
    q, s = r["quality"], r["support"]
    assert q["metadata_total"] == 239
    assert q["metadata_eligible"] == 193
    assert q["metadata_excluded"]["effort_camera_threshold"] == 46
    assert q["response_eligible_studies_atleast_five_species"] == 154
    assert (s["discovery_studies"], s["validation_studies"]) == (121, 33)
    assert (s["discovery_landscapes"], s["validation_landscapes"]) == (51, 14)
    assert (s["discovery_pairs"], s["validation_pairs"]) == (7260, 528)
    assert s["discovery_pairs"] == 121 * 120 // 2
    assert s["validation_pairs"] == 33 * 32 // 2


def test_negative_heldout_environment_increment_is_preserved():
    p = load()["primary"]
    assert p["fit_base"]["predictors"] == ["geography", "effort"]
    assert p["fit_full"]["predictors"] == ["geography", "effort", "environment"]
    assert p["fit_base"]["alpha"] == p["fit_full"]["alpha"] == 5
    assert p["fit_full"]["coef"][-1] == pytest.approx(0.01990317591274089)
    assert p["mae_geography_effort_only"] == pytest.approx(0.13308294408471527)
    assert p["mae_geography_effort_environment"] == pytest.approx(0.13616314973575872)
    assert p["heldout_mae_gain_baseline_minus_full"] == pytest.approx(
        p["mae_geography_effort_only"] - p["mae_geography_effort_environment"]
    )
    assert p["heldout_mae_gain_baseline_minus_full"] < 0
    assert p["positive_rule_mae_0_02_and_positive_environment_coefficient"] is False


def test_secondary_subgroups_and_caveats_not_promoted():
    r = load()
    assert r["secondary"]["same_country"]["heldout_pairs"] == 107
    assert r["secondary"]["different_country"]["heldout_pairs"] == 421
    assert sum(r["secondary"][g]["heldout_pairs"] for g in ("same_country", "different_country")) == 528
    assert all(r["secondary"][g]["mae_gain"] < 0 for g in ("same_country", "different_country"))
    assert r["overlap"]["shared_named_sources_discovery_validation"] == 7
    assert r["quality"]["domestic_category_not_excluded_per_frozen_design"] is True
    assert all(r["inference_limits"].values())