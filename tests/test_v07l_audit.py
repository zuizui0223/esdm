from esdm.validate.v07l_audit import (
    V07L_EXCLUDED_CELLS,
    V07L_LOW_HEADROOM_MAX_SD,
    V07L_LOW_HEADROOM_MIN_RATIO,
    V07L_TRIGGER_RATIO,
    evaluate_v07l_audit,
)


def test_v07l_audit_selects_fresh_extreme_headroom_cells():
    audit = evaluate_v07l_audit()

    assert audit.trigger_ratio == 0.80
    assert audit.eligible_fresh_cells >= 4
    assert len(audit.high_headroom) == 2
    assert len(audit.low_headroom) == 2

    for row in (*audit.high_headroom, *audit.low_headroom):
        assert (
            row.psi0,
            row.gamma,
            row.epsilon,
        ) not in V07L_EXCLUDED_CELLS
        assert row.transferred_conditioning_pass
        assert row.local_eligible

    assert max(
        row.oracle_to_transferred_ratio
        for row in audit.high_headroom
    ) <= V07L_TRIGGER_RATIO
    assert min(
        row.oracle_to_transferred_ratio
        for row in audit.low_headroom
    ) >= V07L_LOW_HEADROOM_MIN_RATIO
    assert max(
        row.transferred_worst_sd
        for row in audit.low_headroom
    ) <= V07L_LOW_HEADROOM_MAX_SD


def test_v07l_audit_order_spans_large_and_small_reoptimization_headroom():
    audit = evaluate_v07l_audit()

    assert max(
        row.oracle_to_transferred_ratio
        for row in audit.high_headroom
    ) < min(
        row.oracle_to_transferred_ratio
        for row in audit.low_headroom
    )
