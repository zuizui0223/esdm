import importlib.util
import os

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


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


def test_v05b_training_has_three_source_only_perturbation_levels():
    from esdm.validate.v05b_perturbation import build_v05b_fixture

    fixture = build_v05b_fixture(_sample_csv(), world="interaction_null")
    values = {
        fixture.perturbation_by_space[space]
        for space in fixture.train_spaces
    }

    assert values == {-1.0, 0.0, 1.0}
    assert all(
        fixture.perturbation_by_space[space] == 0.0
        for space in fixture.heldout_spaces
    )


def test_v05b_perturbation_enters_source_but_not_focal_process():
    from esdm.validate.v05b_perturbation import build_v05b_fixture

    fixture = build_v05b_fixture(_sample_csv(), world="directed_positive")
    source = fixture.model.species["source"][0]
    focal = fixture.model.species["focal"]

    assert "source_perturbation" in source.covariates
    assert all(
        "source_perturbation" not in getattr(process, "requires", frozenset())
        for process in focal
    )
    assert fixture.generating_theta["source"]["source_beta_perturbation"] == 1.0


def test_v05b_worlds_still_differ_only_in_partner_beta():
    from esdm.validate.v05b_perturbation import build_v05b_fixture

    text = _sample_csv()
    directed = build_v05b_fixture(text, world="directed_positive")
    null = build_v05b_fixture(text, world="interaction_null")

    assert directed.generating_theta["focal"]["beta_partner"] == 0.80
    assert null.generating_theta["focal"]["beta_partner"] == 0.0
    assert directed.perturbation_by_space == null.perturbation_by_space


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX unavailable")
def test_v05b_identification_evaluator_is_guarded():
    if os.environ.get("ESDM_RUN_V05B_QUALIFICATION") != "1":
        pytest.skip("requires explicit v0.5b qualification authorization")

    from esdm.validate.v05b_gate import evaluate_v05b_identification

    result = evaluate_v05b_identification(_sample_csv())
    assert result.directed_structural is True
    assert result.null_structural is True
