import json

from scripts.aggregate_field1 import (
    EXPECTED_FIT_COUNT,
    EXPECTED_SHARD_COUNT,
    REPLICATES,
    aggregate_field1_shards,
    main as aggregate_main,
)
from esdm.validate.field1_known_truth import (
    make_field1_mean_covariance_factorial,
    make_field1_primary_worlds,
)
from esdm.validate.field1_run import field1_required_fit_plan


def _worlds():
    return (
        *make_field1_primary_worlds(),
        *make_field1_mean_covariance_factorial(),
    )


def _write_passing_shards(root):
    for world in _worlds():
        positive = set(world.expected_positive_comparisons)
        comparisons = (
            *world.expected_positive_comparisons,
            *world.expected_null_comparisons,
        )
        for replicate in range(REPLICATES):
            payload = {
                "schema": "esdm.field1.replicate_result.v1",
                "world_id": world.world_id,
                "replicate": replicate,
                "gains": [
                    {
                        "candidate_model": candidate,
                        "reference_model": reference,
                        "holdout": holdout,
                        "gain": (
                            0.012
                            if (candidate, reference, holdout) in positive
                            else 0.0
                        ),
                    }
                    for candidate, reference, holdout in comparisons
                ],
                "fits": [
                    {
                        "holdout": holdout,
                        "model_id": model_id,
                        "divergences": 0,
                    }
                    for holdout, model_id in field1_required_fit_plan(
                        world.world_id
                    )
                ],
            }
            path = root / world.world_id / f"{replicate}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )


def test_field1_aggregator_requires_and_accepts_complete_frozen_shard_set(tmp_path):
    _write_passing_shards(tmp_path)
    result = aggregate_field1_shards(tmp_path)

    assert result["status"] == "PASS"
    assert result["shard_count"] == EXPECTED_SHARD_COUNT == 9 * 16
    assert result["fit_count"] == EXPECTED_FIT_COUNT == 704
    assert result["k6_distance_match_passed"] is True
    assert result["h2_barrier_transfer_passed"] is True
    assert (
        result["h2_barrier_transfer_geometry"]["training_barrier_edge_count"]
        >= 1
    )
    assert (
        result["h2_barrier_transfer_geometry"][
            "heldout_boundary_barrier_edge_count"
        ]
        >= 1
    )
    assert all(result["claims"].values())


def test_field1_aggregator_fails_closed_on_missing_shard(tmp_path):
    _write_passing_shards(tmp_path)
    missing = tmp_path / "K4" / "15.json"
    missing.unlink()

    try:
        aggregate_field1_shards(tmp_path)
    except ValueError as exc:
        assert "missing shards" in str(exc)
    else:
        raise AssertionError("missing FIELD1 shard must fail closed")



def test_field1_aggregator_rejects_extra_fit_that_could_dilute_divergence_rate(tmp_path):
    _write_passing_shards(tmp_path)
    path = tmp_path / "K1" / "0.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["fits"].append(
        {"holdout": "H2", "model_id": "M0", "divergences": 0}
    )
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        aggregate_field1_shards(tmp_path)
    except ValueError as exc:
        assert "fit plan drift" in str(exc)
    else:
        raise AssertionError("extra FIELD1 fit must fail closed")



def test_field1_aggregate_cli_writes_infrastructure_blocked_receipt(
    tmp_path,
    monkeypatch,
):
    shard_dir = tmp_path / "shards"
    shard_dir.mkdir()
    output = tmp_path / "FIELD1_QUALIFICATION_RESULT.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "aggregate_field1.py",
            "--shard-dir",
            str(shard_dir),
            "--output",
            str(output),
        ],
    )

    code = aggregate_main()
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert code == 2
    assert payload["status"] == "INFRASTRUCTURE_BLOCKED"
    assert payload["scientific_decision"] is None
    assert payload["error_type"] == "ValueError"
    assert "missing shards" in payload["reason"]
