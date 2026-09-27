import json

from scripts.aggregate_field1 import (
    EXPECTED_FIT_COUNT,
    EXPECTED_SHARD_COUNT,
    REPLICATES,
    aggregate_field1_shards,
)
from esdm.validate.field1_known_truth import (
    make_field1_mean_covariance_factorial,
    make_field1_primary_worlds,
)


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
                        "holdout": "H1",
                        "model_id": "M0",
                        "divergences": 0,
                    }
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
