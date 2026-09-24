from esdm.validate.v05e_run import V05ESummary, V05EWorldSummary


def _world(world, **overrides):
    values = dict(
        world=world,
        replicates=16,
        mean_beta_bias=0.0,
        beta_coverage=0.875,
        beta_positive_interval_rate=0.0,
        beta_nonzero_interval_rate=0.125,
        mean_event_bias=0.05,
        event_coverage=0.875,
        positive_event_rate=1.0,
        predictive_tier_rate=0.0,
        realized_tier_rate=1.0,
        functional_or_higher_rate=0.0,
        total_divergences=0,
    )
    values.update(overrides)
    return V05EWorldSummary(**values)


def _summary():
    return V05ESummary(
        worlds={
            "hidden_event_silent": _world(
                "hidden_event_silent",
                positive_event_rate=0.125,
                predictive_tier_rate=0.875,
                realized_tier_rate=0.125,
                mean_event_bias=5.0,
                event_coverage=0.0,
                beta_nonzero_interval_rate=1.0,
                beta_positive_interval_rate=1.0,
            ),
            "realized_only": _world("realized_only"),
            "directed_realized": _world(
                "directed_realized",
                beta_positive_interval_rate=0.875,
                beta_nonzero_interval_rate=0.875,
            ),
        },
        total_fits=48,
        total_divergences=0,
    )


def test_v05e_gate_accepts_evidence_separation_without_requiring_hidden_beta_repair():
    from esdm.validate.v05e_gate import evaluate_v05e_gate

    decision = evaluate_v05e_gate(_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_v05e_gate_rejects_functional_self_promotion():
    from esdm.validate.v05e_gate import evaluate_v05e_gate

    summary = _summary()
    directed = summary.worlds["directed_realized"]
    bad = V05ESummary(
        worlds={
            **summary.worlds,
            "directed_realized": V05EWorldSummary(
                **{
                    **directed.__dict__,
                    "functional_or_higher_rate": 0.0625,
                }
            ),
        },
        total_fits=summary.total_fits,
        total_divergences=summary.total_divergences,
    )
    assert evaluate_v05e_gate(bad).passed is False
