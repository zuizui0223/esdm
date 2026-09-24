import pytest

from esdm.authorization import (
    InteractionEventRecord,
    authorize_interaction_event,
)


def test_pair_event_positive_is_authorized_for_exact_edge():
    event = authorize_interaction_event(
        InteractionEventRecord(
            "source",
            "focal",
            "evt-1",
            "positive",
        )
    )

    assert event.source == "source"
    assert event.target == "focal"
    assert event.evidence_state == "positive"
    assert event.is_positive is True


def test_pair_event_negative_still_requires_negative_gate():
    blocked = authorize_interaction_event(
        InteractionEventRecord(
            "source",
            "focal",
            "evt-2",
            "negative",
            negative_gate_passed=False,
        )
    )
    opened = authorize_interaction_event(
        InteractionEventRecord(
            "source",
            "focal",
            "evt-3",
            "negative",
            negative_gate_passed=True,
        )
    )

    assert blocked.evidence_state == "unavailable"
    assert opened.evidence_state == "negative"


def test_pair_event_rejects_self_edge():
    with pytest.raises(ValueError, match="must differ"):
        InteractionEventRecord("sp", "sp", "evt", "positive")
