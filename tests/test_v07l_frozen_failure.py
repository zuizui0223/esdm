from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "validation" / "V07L_FROZEN_RESULTS.json"
AUDIT = ROOT / "docs" / "validation" / "V07L_FAILURE_AUDIT_V1.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v07l_frozen_result_is_scientific_fail_not_infrastructure_failure():
    result = _read(RESULT)

    assert result["status"] == "FAIL"
    assert result["one_shot"]["workflow_run_id"] == 36223841269
    assert result["one_shot"]["run_attempt"] == 1
    assert result["one_shot"]["infrastructure_block"] is None
    assert result["one_shot"]["artifact_id"] == 10900450588
    assert result["summary"]["replicates"] == 64
    assert result["summary"]["fit_count"] == 192
    assert result["summary"]["total_divergences"] == 0
    assert len(result["failed_checks"]) == 8


def test_v07l_failure_contains_classification_and_recovery_failures():
    result = _read(RESULT)
    failed = {row["name"]: row for row in result["failed_checks"]}

    assert failed["threshold_below:trigger_rate"]["observed"] == 0.5625
    assert (
        failed["threshold_below:actual_material_headroom_rate"]["observed"]
        == 0.6875
    )
    assert failed["trigger_sensitivity"]["observed"] == 0.7407407407407407
    assert failed["mean_policy_regret"]["observed"] == 0.055624395981999294

    recovery = [
        name for name in failed
        if ":policy_bias:" in name
    ]
    assert len(recovery) == 4


def test_exhaustive_threshold_audit_rules_out_threshold_only_rescue():
    audit = _read(AUDIT)
    scan = audit["scalar_threshold_exhaustive_audit"]
    invariant = audit["invariant_failure"]

    assert scan["action_equivalence_candidate_count"] == 119
    assert scan["any_threshold_recovery_guardrails_pass"] is False
    assert scan["threshold_only_rescue_possible"] is False
    assert invariant["threshold_below_actual_material_headroom_rate"] == 0.6875
    assert invariant["frozen_required_rate"] == 0.75
    assert invariant["depends_on_trigger_threshold"] is False


def test_perfect_headroom_classifier_still_fails_absolute_recovery():
    audit = _read(AUDIT)
    oracle = audit["oracle_material_headroom_policy"]

    assert oracle["trigger_sensitivity"] == 1.0
    assert oracle["trigger_specificity"] == 1.0
    assert oracle["mean_policy_regret"] == 0.0
    assert oracle["recovery_guardrails_pass"] is False

    failed = {
        (row["world"], row["target"]): row["observed"]
        for row in oracle["failed_recovery_checks"]
    }
    assert failed[("threshold_above", "sp.occupancy.psi0_logit")] > 0.20
    assert failed[("threshold_above", "sp.occupancy.gamma_logit")] > 0.20
    assert failed[("threshold_above", "sp.occupancy.epsilon_logit")] > 0.20


def test_v07l_next_step_is_not_post_result_trigger_retuning():
    result = _read(RESULT)
    audit = _read(AUDIT)

    assert result["next_development_boundary"]["same_v07l_rerun_allowed"] is False
    assert (
        result["next_development_boundary"][
            "post_result_trigger_retune_inside_v07l_allowed"
        ]
        is False
    )
    assert audit["conclusion"]["trigger_retune_is_sufficient"] is False
    assert audit["conclusion"]["placement_only_policy_family_is_sufficient"] is False
    assert audit["conclusion"]["next_confirmatory_program_requires_fresh_worlds"] is True
    assert (
        audit["conclusion"]["next_development_need"]
        == "separate absolute recovery adequacy from relative placement headroom"
    )
