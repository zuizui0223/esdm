from esdm.validate.v05b_gate import V05BIdentificationSummary


def _passing():
    return V05BIdentificationSummary(
        directed_structural=True,
        directed_practical=True,
        null_structural=True,
        null_practical=True,
        directed_target_sd=0.10,
        null_target_sd=0.12,
    )


def test_v05b_gate_requires_all_four_terms():
    from dataclasses import replace
    from esdm.validate.v05b_gate import evaluate_v05b_gate

    assert evaluate_v05b_gate(_passing()).passed is True

    for field in (
        "directed_structural",
        "directed_practical",
        "null_structural",
        "null_practical",
    ):
        assert evaluate_v05b_gate(
            replace(_passing(), **{field: False})
        ).passed is False
