from esdm.claims import ProcessSupportSet, refine_process_support_set
from esdm.process import LinearSuitability
from esdm.summarize import alpha_diversity_q1, network_beta_q1
from esdm.validate import point_transfer_ceiling


def test_process_namespace_is_generative_and_process_support_lives_in_claims():
    process = LinearSuitability((), "alpha", {})
    assert process.name == "suitability"
    base = ProcessSupportSet(("shared_environment", "competition"))
    refined = refine_process_support_set(base, (), required_separator_ids=("sep",))
    assert refined.refined.members == base.members


def test_previous_summary_and_validation_primitives_remain_available_downstream():
    assert callable(alpha_diversity_q1)
    assert callable(network_beta_q1)
    assert callable(point_transfer_ceiling)
