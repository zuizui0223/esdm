from dataclasses import fields
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability


def _models():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    stream = PresenceOnly(
        name="records",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    full = Model(grid, {"sp": (process,)}, (stream,))
    knockout = full.knockout("sp", "suitability")
    covariates = {
        grid.keys[0]: {"x": -1.0},
        grid.keys[1]: {"x": 1.0},
    }
    data = {
        "records": {
            "sp": {
                grid.keys[0]: 0,
                grid.keys[1]: 6,
            }
        }
    }
    return full, knockout, covariates, data


def test_evidence_types_are_public_and_do_not_encode_claim_promotion():
    from esdm.validate import (
        EvidenceBundle,
        IdentificationEvidence,
        KnockoutEvidence,
        TransferEvidence,
    )

    for cls in (IdentificationEvidence, KnockoutEvidence, TransferEvidence, EvidenceBundle):
        names = {field.name for field in fields(cls)}
        assert "claim_status" not in names
        assert "tier" not in names
        assert "supported" not in names


def test_identification_diagnostic_is_wrapped_as_evidence_without_support_claim():
    from esdm.identify import IdentificationStatus
    from esdm.validate import diagnose_identification

    full, _knockout, covariates, _data = _models()
    evidence = diagnose_identification(
        full,
        covariates,
        theta={"sp": {"intercept": 0.2, "beta_x": 0.8}},
        theta_obs={},
        target="sp.suitability.beta_x",
        practical=False,
    )
    assert evidence.target == "sp.suitability.beta_x"
    assert evidence.structural.status is IdentificationStatus.IDENTIFIED
    assert evidence.practical is None


def test_compare_knockout_scores_real_posterior_rate_draws():
    from esdm.validate import compare_knockout

    full, knockout, covariates, data = _models()
    evidence = compare_knockout(
        full,
        {
            "sp.suitability.intercept": [math.log(2.0)],
            "sp.suitability.beta_x": [1.0],
        },
        knockout,
        {"sp.suitability.intercept": [math.log(2.0)]},
        full_covariates=covariates,
        knockout_covariates=covariates,
        data=data,
        stream_name="records",
        species="sp",
    )
    assert evidence.n_contexts == 2
    assert evidence.full_log_score > evidence.knockout_log_score
    assert evidence.gain == evidence.full_log_score - evidence.knockout_log_score


def test_evaluate_transfer_uses_same_heldout_scoring_primitive():
    from esdm.validate import evaluate_transfer

    full, knockout, covariates, data = _models()
    evidence = evaluate_transfer(
        full,
        {
            "sp.suitability.intercept": [math.log(2.0)],
            "sp.suitability.beta_x": [1.0],
        },
        knockout,
        {"sp.suitability.intercept": [math.log(2.0)]},
        candidate_covariates=covariates,
        reference_covariates=covariates,
        data=data,
        stream_name="records",
        species="sp",
        heldout_label="east",
    )
    assert evidence.heldout_label == "east"
    assert evidence.n_contexts == 2
    assert evidence.gain > 0.0
