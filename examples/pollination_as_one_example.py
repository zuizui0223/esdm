"""Pollination is one domain example of the generic interaction-opportunity API.

Nothing in the runtime package knows that these labels are floral or pollinator
states; they are ordinary source/target state names passed to the generic kernel.
"""

from esdm.interaction import interaction_opportunity


potential_opportunity = interaction_opportunity(
    {"not_flowering": 0.3, "flowering": 0.7},
    {"inactive": 0.4, "foraging": 0.6},
    {
        ("not_flowering", "inactive"): 0.0,
        ("not_flowering", "foraging"): 0.0,
        ("flowering", "inactive"): 0.0,
        ("flowering", "foraging"): 0.9,
    },
)

print(f"potential interaction opportunity: {potential_opportunity:.3f}")
