from esdm.validate.v06c_gate import evaluate_v06c_gate
from esdm.validate.v06c_qualification import V06CQualification
from esdm.validate.v06c_run import V06CSummary
from esdm.validate.v06a_fixture import V06A_RECOVERY_TRUTH
from esdm.validate.v06c_fixture import V06C_ACCESS_TARGETS


def _summary():
    return V06CSummary(
        replicates=16,
        fit_count=32,
        direct_mean_biases={target: 0.02 for target in V06A_RECOVERY_TRUTH},
        matched_mean_biases={target: 0.10 for target in V06A_RECOVERY_TRUTH},
        direct_coverages={target: 0.875 for target in V06A_RECOVERY_TRUTH},
        matched_coverages={target: 0.875 for target in V06A_RECOVERY_TRUTH},
        direct_lower_sd_rates={target: 0.9375 for target in V06C_ACCESS_TARGETS},
        mean_sd_ratios={target: 0.60 for target in V06C_ACCESS_TARGETS},
        mean_direct_aux_count=280.0,
        mean_matched_aux_count=280.0,
        mean_heldout_gain_direct_minus_matched=0.0,
        direct_better_heldout_rate=0.5,
        total_divergences=0,
    )


def test_v06c_gate_accepts_budget_matched_information_advantage():
    q = V06CQualification(
        relative_budget_error=1e-15,
        expected_direct_aux_count=280.0,
        expected_matched_aux_count=280.0,
        direct_evidence={},
        matched_evidence={},
        access_sd_proxy_ratios={target: 0.40 for target in V06C_ACCESS_TARGETS},
    )
    object.__setattr__(q, "direct_evidence", {
        target: type("E", (), {
            "structural": type("S", (), {"status": __import__(
                "esdm.identify", fromlist=["IdentificationStatus"]
            ).IdentificationStatus.IDENTIFIED})(),
            "practical": type("P", (), {"weak": False})(),
        })()
        for target in V06A_RECOVERY_TRUTH
    })
    object.__setattr__(q, "matched_evidence", {
        target: type("E", (), {
            "structural": type("S", (), {"status": __import__(
                "esdm.identify", fromlist=["IdentificationStatus"]
            ).IdentificationStatus.IDENTIFIED})(),
            "practical": type("P", (), {"weak": True})(),
        })()
        for target in V06A_RECOVERY_TRUTH
    })
    assert evaluate_v06c_gate(q, _summary()).passed is True
