import importlib.util
import os

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None
R3A_OUTCOME_ENABLED = os.environ.get("ESDM_RUN_R3A_QUALIFICATION") == "1"


def _sample_csv(rows=130):
    header = "id,city,station,average,latitude,longitude,state,total19"
    lines = [header]
    for i in range(rows):
        latitude = 22.0 + (i % 31) * 0.75
        longitude = -154.0 + (i % 43) * 2.25
        average = 45.0 + ((i * 7) % 29) * 1.3
        total19 = 35.0 + (i % 13) * 1.7
        lines.append(
            f"S{i:04d},City{i},Station{i},{average:.3f},"
            f"{latitude:.4f},{longitude:.4f},ST,{total19:.1f}"
        )
    return "\n".join(lines) + "\n"


@pytest.mark.skipif(
    not JAX_AVAILABLE or not R3A_OUTCOME_ENABLED,
    reason="R3a outcome test requires explicit authorization environment",
)
def test_r3a_evaluator_returns_all_three_profile_evidence_groups():
    from esdm.validate.v04_r2_gate import R2_IDENTIFICATION_TARGETS
    from esdm.validate.v04_r3a_gate import evaluate_v04_r3a_identification

    result = evaluate_v04_r3a_identification(_sample_csv())

    assert len(R2_IDENTIFICATION_TARGETS) == 13
    assert len(result.positive_anchor_evidence) == 3
    assert all(len(anchor) == 13 for anchor in result.positive_anchor_evidence)
    assert len(result.sparse_anchor_evidence) == 3
    assert all(len(anchor) == 13 for anchor in result.sparse_anchor_evidence)
    assert len(result.unknown_anchor_evidence) == 3
    assert all(len(anchor) == 2 for anchor in result.unknown_anchor_evidence)


def test_r3a_qualification_summary_counts_design_not_observed_records(monkeypatch):
    from types import SimpleNamespace
    from esdm.validate import v04_r3a_gate

    class ZeroEffort:
        @staticmethod
        def at(key):
            return 0.0

    fake = SimpleNamespace(
        train_spaces=("a", "b"),
        calibrated_spaces=tuple(f"c{i}" for i in range(18)),
        annotated_spaces=tuple(f"a{i}" for i in range(36)),
        annotated_times=tuple((15 + i, 0) for i in range(12)),
        model=SimpleNamespace(
            domain=SimpleNamespace(
                keys=(),
                doy=(15, 75, 135, 195, 255, 315),
                hour=(0, 6, 12, 18),
            ),
            streams=(
                SimpleNamespace(),
                SimpleNamespace(effort=ZeroEffort()),
                SimpleNamespace(effort=ZeroEffort()),
            ),
        ),
    )
    monkeypatch.setattr(
        v04_r3a_gate,
        "build_v04_r3a_fixture",
        lambda source: fake,
    )
    identification = SimpleNamespace(
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
    )

    summary = v04_r3a_gate.qualification_summary("ignored", identification)

    assert summary.annotated_space_count == 36
    assert summary.annotated_time_count == 12



def test_r3a_qualification_summary_counts_actual_stream_exposure(monkeypatch):
    from types import SimpleNamespace

    from esdm.validate import v04_r3a_gate

    class FakeEffort:
        def __init__(self, exposed):
            self._exposed = set(exposed)

        def at(self, key):
            return 1.0 if key in self._exposed else 0.0

    keys = (
        ("a", 15, 0),
        ("a", 15, 6),
        ("b", 15, 0),
        ("b", 15, 6),
    )
    annotated_exposed = {keys[0], keys[1], keys[2]}
    calibrated_exposed = {keys[0], keys[2]}
    fake = SimpleNamespace(
        train_spaces=("a", "b"),
        calibrated_spaces=("a",),
        annotated_spaces=("a", "b"),
        annotated_times=((15, 0), (15, 6)),
        model=SimpleNamespace(
            domain=SimpleNamespace(
                keys=keys,
                doy=(15,),
                hour=(0, 6),
            ),
            streams=(
                SimpleNamespace(),
                SimpleNamespace(effort=FakeEffort(calibrated_exposed)),
                SimpleNamespace(effort=FakeEffort(annotated_exposed)),
            ),
        ),
    )
    monkeypatch.setattr(
        v04_r3a_gate,
        "build_v04_r3a_fixture",
        lambda source: fake,
    )
    identification = SimpleNamespace(
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
    )

    summary = v04_r3a_gate.qualification_summary("ignored", identification)

    assert summary.annotated_context_count == 3
    assert summary.calibrated_context_count == 2
