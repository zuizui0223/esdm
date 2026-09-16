import pytest

from esdm.authorization import ObservationRecord, authorize_observation


def test_positive_observation_is_authorized_without_negative_gate():
    result = authorize_observation(
        ObservationRecord("edge:a>b", "positive", negative_gate_passed=False)
    )
    assert result.evidence_state == "positive"
    assert result.reason == "resolved_positive"


def test_negative_requires_explicit_gate():
    blocked = authorize_observation(
        ObservationRecord("edge:a>b", "negative", negative_gate_passed=False)
    )
    opened = authorize_observation(
        ObservationRecord("edge:a>b", "negative", negative_gate_passed=True)
    )
    assert blocked.evidence_state == "unavailable"
    assert blocked.reason == "negative_not_authorized"
    assert opened.evidence_state == "negative"
    assert opened.reason == "resolved_negative_authorized"


@pytest.mark.parametrize(
    "raw_state",
    ["missing", "unresolved", "device_failure", "occluded"],
)
def test_failure_or_unresolved_states_are_unavailable(raw_state):
    result = authorize_observation(
        ObservationRecord("edge:a>b", raw_state, negative_gate_passed=True)
    )
    assert result.evidence_state == "unavailable"
    assert result.reason == f"raw_state_{raw_state}"


def test_unknown_raw_state_fails_closed():
    with pytest.raises(ValueError):
        ObservationRecord("edge:a>b", "probably_absent", negative_gate_passed=True)
