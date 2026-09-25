import pytest

from esdm.transfer import build_v05f_directed_interaction_odsp_bundle


def _result():
    records = []
    for world in ("interaction", "measured_shared_null"):
        for replicate in range(16):
            if world == "interaction":
                knockout, full = -2.0, -1.6
            else:
                knockout, full = -2.0, -2.02
            records.append(
                {
                    "world": world,
                    "replicate": replicate,
                    "truth_beta": 0.75 if world == "interaction" else 0.0,
                    "posterior_mean": 0.75 if world == "interaction" else 0.0,
                    "interval_low": 0.5 if world == "interaction" else -0.1,
                    "interval_high": 0.9 if world == "interaction" else 0.1,
                    "full_heldout_log_score": full,
                    "partner_knockout_heldout_log_score": knockout,
                    "full_divergences": 0,
                    "knockout_divergences": 0,
                }
            )
    return {
        "schema": "esdm.v05f.interaction_transfer_replication.v1",
        "status": "PASS",
        "git_sha": "future-v05f",
        "infrastructure_block": None,
        "replicates": records,
    }


def test_v05f_binding_exports_interaction_world_only():
    bundle = build_v05f_directed_interaction_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_v05f_directed_interaction_transfer_v1"
    assert bundle.contract["levels"] == [
        {
            "name": "measured_environment",
            "information": ["measured_environment"],
            "score_column": "score__measured_environment",
        },
        {
            "name": "measured_environment_directed_partner",
            "information": ["measured_environment", "directed_partner_latent"],
            "score_column": "score__measured_environment_directed_partner",
        },
    ]
    assert len(bundle.rows) == 16
    assert bundle.rows[0]["score__measured_environment"] == pytest.approx(-2.0)
    assert bundle.rows[0]["score__measured_environment_directed_partner"] == pytest.approx(-1.6)
    assert bundle.manifest["group_semantics"] == (
        "independent interaction-world known-truth replicate"
    )


def test_v05f_binding_never_mixes_null_world_into_transfer_population():
    bundle = build_v05f_directed_interaction_odsp_bundle(_result())

    assert {row["group"] for row in bundle.rows} == {str(i) for i in range(16)}
    assert all(
        row["score__measured_environment_directed_partner"]
        - row["score__measured_environment"]
        > 0
        for row in bundle.rows
    )


def test_v05f_binding_rejects_incomplete_or_blocked_results():
    incomplete = _result()
    incomplete["replicates"] = [
        row
        for row in incomplete["replicates"]
        if not (row["world"] == "interaction" and row["replicate"] == 15)
    ]
    with pytest.raises(ValueError, match="exactly 16 interaction-world records"):
        build_v05f_directed_interaction_odsp_bundle(incomplete)

    blocked = _result()
    blocked["status"] = "INFRASTRUCTURE_BLOCKED"
    blocked["infrastructure_block"] = {"reason": "blocked"}
    with pytest.raises(ValueError, match="completed scientific result"):
        build_v05f_directed_interaction_odsp_bundle(blocked)
