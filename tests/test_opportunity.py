import pytest

from esdm.interaction.opportunity import interaction_opportunity


def test_interaction_opportunity_is_one_for_matching_deterministic_states():
    value = interaction_opportunity(
        {"state_a": 1.0},
        {"state_b": 1.0},
        {("state_a", "state_b"): 1.0},
    )
    assert value == pytest.approx(1.0)


def test_interaction_opportunity_is_zero_for_incompatible_states():
    value = interaction_opportunity(
        {"state_a": 1.0},
        {"state_b": 1.0},
        {("state_a", "state_b"): 0.0},
    )
    assert value == pytest.approx(0.0)


def test_interaction_opportunity_matches_manual_weighted_sum():
    value = interaction_opportunity(
        {"s1": 0.25, "s2": 0.75},
        {"t1": 0.60, "t2": 0.40},
        {
            ("s1", "t1"): 1.0,
            ("s1", "t2"): 0.0,
            ("s2", "t1"): 0.5,
            ("s2", "t2"): 0.2,
        },
    )
    assert value == pytest.approx(0.435)


def test_same_generic_function_accepts_domain_example_labels_without_special_logic():
    neutral = interaction_opportunity(
        {"source_ready": 1.0},
        {"target_ready": 1.0},
        {("source_ready", "target_ready"): 0.8},
    )
    domain_example = interaction_opportunity(
        {"flowering": 1.0},
        {"foraging": 1.0},
        {("flowering", "foraging"): 0.8},
    )
    assert neutral == pytest.approx(domain_example)


def test_interaction_opportunity_rejects_out_of_range_compatibility():
    with pytest.raises(ValueError):
        interaction_opportunity(
            {"a": 1.0},
            {"b": 1.0},
            {("a", "b"): 1.2},
        )
