from esdm.validate.v07j_fixture import V07J_TARGET_WORLDS
from esdm.validate.v07k_fixture import V07K_WORLD_PROBABILITIES
from esdm.validate.v07l_fixture import V07L_WORLD_PROBABILITIES
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


def _probability_triples(rows):
    return {
        (row["psi0"], row["gamma"], row["epsilon"])
        for row in rows.values()
    }


def test_v07m_world_probabilities_are_fresh_against_prior_confirmatory_worlds():
    current = _probability_triples(V07M_WORLD_PROBABILITIES)
    prior = (
        _probability_triples(V07L_WORLD_PROBABILITIES)
        | _probability_triples(V07J_TARGET_WORLDS)
        | _probability_triples(V07K_WORLD_PROBABILITIES)
    )

    assert current.isdisjoint(prior)
