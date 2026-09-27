import pytest

from esdm.process import (
    ProcessSupportSet,
    SeparatorEvidence,
    refine_process_support_set,
)


def test_support_set_accepts_empty_singleton_and_multi_member_states():
    assert ProcessSupportSet(()).members == ()
    assert ProcessSupportSet(("competition",)).members == ("competition",)
    assert ProcessSupportSet(("shared_environment", "competition")).members == (
        "shared_environment",
        "competition",
    )


def test_support_set_rejects_duplicate_members():
    with pytest.raises(ValueError):
        ProcessSupportSet(("competition", "competition"))


def test_missing_or_nonexcluding_separator_evidence_retains_member():
    base = ProcessSupportSet(("shared_environment", "competition"))
    evidence = (
        SeparatorEvidence(
            process="competition",
            separator_id="field",
            evidence_state="exclude",
            qualified=True,
            source_disjoint=True,
            preoutcome_frozen=True,
        ),
        SeparatorEvidence(
            process="shared_environment",
            separator_id="field",
            evidence_state="compatible",
            qualified=True,
            source_disjoint=True,
            preoutcome_frozen=True,
        ),
        SeparatorEvidence(
            process="shared_environment",
            separator_id="trait",
            evidence_state="indeterminate",
            qualified=True,
            source_disjoint=True,
            preoutcome_frozen=True,
        ),
    )
    result = refine_process_support_set(
        base,
        evidence,
        required_separator_ids=("field", "trait"),
    )
    assert result.refined.members == base.members
    assert result.removed == ()
    assert result.member_decisions["competition"] == "retain_missing_separator"
    assert result.member_decisions["shared_environment"] == "retain_nonexclusion"


def test_unavailable_or_unqualified_evidence_retains_member():
    base = ProcessSupportSet(("competition",))
    unavailable = (
        SeparatorEvidence(
            "competition", "field", "exclude", True, True, True
        ),
        SeparatorEvidence(
            "competition", "trait", "unavailable", True, True, True
        ),
    )
    result = refine_process_support_set(
        base, unavailable, required_separator_ids=("field", "trait")
    )
    assert result.refined.members == ("competition",)

    unqualified = (
        SeparatorEvidence(
            "competition", "field", "exclude", True, True, True
        ),
        SeparatorEvidence(
            "competition", "trait", "exclude", False, True, True
        ),
    )
    result = refine_process_support_set(
        base, unqualified, required_separator_ids=("field", "trait")
    )
    assert result.refined.members == ("competition",)
    assert result.member_decisions["competition"] == "retain_unqualified_separator"


def test_member_removed_only_by_unanimous_qualified_independent_preoutcome_exclusion():
    base = ProcessSupportSet(("shared_environment", "competition", "mutualism"))
    evidence = tuple(
        SeparatorEvidence(
            process="shared_environment",
            separator_id=separator,
            evidence_state="exclude",
            qualified=True,
            source_disjoint=True,
            preoutcome_frozen=True,
        )
        for separator in ("field", "trait")
    )
    result = refine_process_support_set(
        base,
        evidence,
        required_separator_ids=("field", "trait"),
    )
    assert result.refined.members == ("competition", "mutualism")
    assert result.removed == ("shared_environment",)
    assert result.contracted is True


def test_source_reuse_or_postoutcome_separator_fails_closed():
    base = ProcessSupportSet(("competition",))
    with pytest.raises(ValueError):
        refine_process_support_set(
            base,
            (
                SeparatorEvidence(
                    "competition", "field", "exclude", True, False, True
                ),
            ),
            required_separator_ids=("field",),
        )
    with pytest.raises(ValueError):
        refine_process_support_set(
            base,
            (
                SeparatorEvidence(
                    "competition", "field", "exclude", True, True, False
                ),
            ),
            required_separator_ids=("field",),
        )


def test_refinement_never_adds_processes():
    base = ProcessSupportSet(("competition",))
    with pytest.raises(ValueError):
        refine_process_support_set(
            base,
            (
                SeparatorEvidence(
                    "mutualism", "field", "exclude", True, True, True
                ),
            ),
            required_separator_ids=("field",),
        )
