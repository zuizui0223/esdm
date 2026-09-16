from esdm.claims import Claim, ClaimStatus
from esdm.core import InteractionEvidenceTier


def test_claim_status_separates_design_and_identification_failures():
    design = Claim(
        status=ClaimStatus.DESIGN_UNINFORMED,
        tier=InteractionEvidenceTier.COAVAILABLE,
        target="activity",
        evidence=("no_stream_path",),
    )
    unidentified = Claim(
        status=ClaimStatus.NOT_IDENTIFIED,
        tier=InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
        target="interaction_beta",
        evidence=("weak_contraction",),
    )
    assert design.status is not unidentified.status
    assert unidentified.tier > design.tier
