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


def test_v05a_worlds_change_only_partner_truth():
    from esdm.validate.v05a_directed import build_v05a_fixture

    text = _sample_csv()
    directed = build_v05a_fixture(text, world="directed_positive")
    null = build_v05a_fixture(text, world="interaction_null")

    assert directed.generating_theta["focal"]["beta_partner"] == 0.80
    assert null.generating_theta["focal"]["beta_partner"] == 0.0

    for species in ("source", "focal"):
        for parameter, value in directed.generating_theta[species].items():
            if parameter == "beta_partner":
                continue
            assert null.generating_theta[species][parameter] == value


def test_v05a_keeps_east_as_true_extrapolation():
    from esdm.validate.v05a_directed import build_v05a_fixture
    from esdm.validate.v05a_run import _extrapolation_integrity

    fixture = build_v05a_fixture(_sample_csv(), world="directed_positive")
    assert _extrapolation_integrity(fixture) is True


def test_v05a_declares_focal_before_source_but_evaluates_source_first():
    from esdm.validate.v05a_directed import build_v05a_fixture

    fixture = build_v05a_fixture(_sample_csv(), world="directed_positive")

    assert tuple(fixture.model.species) == ("focal", "source")
    assert fixture.model._species_topological_order() == ("source", "focal")


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX unavailable")
def test_v05a_beta_is_structurally_identified_in_both_worlds():
    if os.environ.get("ESDM_RUN_V05A_QUALIFICATION") != "1":
        pytest.skip("requires explicit v0.5a qualification authorization")

    from esdm.validate.v05a_gate import evaluate_v05a_identification

    result = evaluate_v05a_identification(_sample_csv())

    assert result.directed_structural is True
    assert result.null_structural is True
