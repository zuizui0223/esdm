"""Generic example: spatial coexistence can hide ecological-state partitioning."""

from esdm.interaction import geographic_overlap, interaction_opportunity, state_overlap


geographic = geographic_overlap([0.5, 0.5], [0.5, 0.5])
state = state_overlap(
    {"resource_1": 0.9, "resource_2": 0.1},
    {"resource_1": 0.1, "resource_2": 0.9},
)
opportunity = interaction_opportunity(
    {"resource_1": 0.9, "resource_2": 0.1},
    {"resource_1": 0.1, "resource_2": 0.9},
    {
        ("resource_1", "resource_1"): 1.0,
        ("resource_1", "resource_2"): 0.2,
        ("resource_2", "resource_1"): 0.2,
        ("resource_2", "resource_2"): 1.0,
    },
)

print(f"geographic overlap: {geographic:.3f}")
print(f"state overlap: {state:.3f}")
print(f"generic state-compatibility opportunity: {opportunity:.3f}")
