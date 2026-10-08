from scripts.decompose_e5_detection_composition import (
    decompose_effective_detection,
)


def test_symmetric_decomposition_exact_with_both_sources_of_variation():
    d=decompose_effective_detection(
        [.8,.2],[.2,.8],
        [.9,.4],[.8,.2],
        [.7,.5],[.6,.9],
    )
    assert abs(d["difference"] - (
        d["conditional_process_component"] +
        d["passage_composition_component"]
    )) < 1e-12


def test_only_behavioral_composition_changes_with_same_hardware():
    d=decompose_effective_detection(
        [.9,.1],[.1,.9],
        [.9,.3],[.9,.3],
        [.9,.7],[.9,.7],
    )
    assert abs(d["conditional_process_component"]) < 1e-12
    assert abs(d["passage_composition_component"]) > .05


def test_identical_passage_composition_is_only_conditional_process():
    d=decompose_effective_detection(
        [.5,.5],[.5,.5],
        [.7,.7],[.4,.7],
        [.8,.8],[.9,.8],
    )
    assert abs(d["passage_composition_component"]) < 1e-12


def test_both_stage_probabilities_required():
    d=decompose_effective_detection(
        [1],[1], [.6],[.6], [.5],[.7]
    )
    assert abs(d["effective_detection_1"]-.3) < 1e-12
    assert abs(d["effective_detection_2"]-.42) < 1e-12


def test_rejects_malformed_inputs():
    import pytest
    with pytest.raises(ValueError):
        decompose_effective_detection([.5,.2],[.2,.8],[.6,.6],[.6,.6],[.8,.8],[.8,.8])
    with pytest.raises(ValueError):
        decompose_effective_detection([1],[1],[1.1],[.5],[.5],[.5])
