from esdm.core.edge import BioticEdge, InteractionEvidenceTier


def test_evidence_tiers_are_strictly_ordered():
    tiers = list(InteractionEvidenceTier)
    assert tiers == [
        InteractionEvidenceTier.COAVAILABLE,
        InteractionEvidenceTier.STATE_COMPATIBLE,
        InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
        InteractionEvidenceTier.REALIZED,
        InteractionEvidenceTier.FUNCTIONAL,
        InteractionEvidenceTier.CAUSAL,
    ]
    assert InteractionEvidenceTier.COAVAILABLE < InteractionEvidenceTier.CAUSAL


def test_biotic_edge_keeps_interaction_type_optional_and_descriptive():
    generic = BioticEdge("taxon_a", "taxon_b", InteractionEvidenceTier.STATE_COMPATIBLE)
    labelled = BioticEdge(
        "taxon_a",
        "taxon_b",
        InteractionEvidenceTier.REALIZED,
        interaction_type="mutualism",
        metadata={"source": "field_observation"},
    )
    assert generic.interaction_type is None
    assert labelled.interaction_type == "mutualism"
    assert labelled.metadata["source"] == "field_observation"
