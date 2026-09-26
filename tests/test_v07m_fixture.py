from esdm.validate.v07m_fixture import (
    V07M_EXPECTED_ACTIONS,
    V07M_ORACLE_PLACEMENTS,
    V07M_WORLD_PROBABILITIES,
    V07M_WORLDS,
    build_v07m_confirm_fixture,
    build_v07m_local_pilot_fixture,
)


def test_v07m_worlds_and_expected_actions_are_frozen():
    assert V07M_WORLDS == (
        "adaptive_large_headroom",
        "adaptive_absolute_rescue",
        "transfer_adequate",
        "abstain_inadequate",
    )
    assert V07M_EXPECTED_ACTIONS == {
        "adaptive_large_headroom": "adaptive",
        "adaptive_absolute_rescue": "adaptive",
        "transfer_adequate": "transferred",
        "abstain_inadequate": "abstain",
    }


def test_v07m_pilot_and_confirmatory_datasets_are_separate():
    for world in V07M_WORLDS:
        pilot = build_v07m_local_pilot_fixture(world)
        confirm = build_v07m_confirm_fixture(
            world,
            V07M_ORACLE_PLACEMENTS[world],
        )

        assert pilot.expected_action == V07M_EXPECTED_ACTIONS[world]
        assert confirm.expected_action == V07M_EXPECTED_ACTIONS[world]
        assert tuple(confirm.heldout_keys) == tuple(confirm.source.heldout_keys)
        assert set(confirm.adaptive_keys).issubset(
            set(confirm.source.training_model.domain.keys)
        )
        assert set(confirm.transferred_keys).issubset(
            set(confirm.source.training_model.domain.keys)
        )


def test_v07m_world_probabilities_are_not_v07l_confirmatory_worlds():
    old = {
        (0.85, 0.25, 0.38),
        (0.85, 0.25, 0.22),
        (0.85, 0.25, 0.08),
        (0.85, 0.65, 0.22),
    }
    current = {
        (row["psi0"], row["gamma"], row["epsilon"])
        for row in V07M_WORLD_PROBABILITIES.values()
    }
    assert old.isdisjoint(current)
