import json

from scripts.aggregate_map1 import (
    EXPECTED_FIT_COUNT,
    EXPECTED_SHARD_COUNT,
    REPLICATES,
    aggregate_map1_shards,
    main as aggregate_main,
)
from esdm.validate.map1_known_truth import make_map1_worlds
from esdm.validate.map1_run import map1_required_fit_plan


def _write_passing(root):
    for world in make_map1_worlds():
        positive = set(world.expected_positive_comparisons)
        comparisons = (
            *world.expected_positive_comparisons,
            *world.expected_null_comparisons,
        )
        for replicate in range(REPLICATES):
            payload = {
                "schema": "esdm.map1.replicate_result.v1",
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
                    for holdout, model_id in map1_required_fit_plan(world.world_id)
                ],
            }
            path = root / world.world_id / f"{replicate}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")


def test_map1_aggregate_accepts_complete_frozen_plan(tmp_path):
    _write_passing(tmp_path)
    result = aggregate_map1_shards(tmp_path)
    assert result["status"] == "PASS"
    assert result["shard_count"] == EXPECTED_SHARD_COUNT == 48
    assert result["fit_count"] == EXPECTED_FIT_COUNT == 128
    assert result["claims"]["COHERENT_MAP_SUPPORTED"] is True


def test_map1_aggregate_rejects_missing_shard(tmp_path):
    _write_passing(tmp_path)
    (tmp_path / "P1" / "15.json").unlink()
    try:
        aggregate_map1_shards(tmp_path)
    except ValueError as exc:
        assert "missing shards" in str(exc)
    else:
        raise AssertionError("missing MAP1 shard must fail closed")


def test_map1_aggregate_rejects_extra_fit(tmp_path):
    _write_passing(tmp_path)
    path = tmp_path / "P1" / "0.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["fits"].append(
        {"holdout": "H1", "model_id": "EXTRA", "divergences": 0}
    )
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        aggregate_map1_shards(tmp_path)
    except ValueError as exc:
        assert "fit plan drift" in str(exc)
    else:
        raise AssertionError("extra MAP1 fit must fail closed")


def test_map1_aggregate_cli_emits_infrastructure_receipt(tmp_path, monkeypatch):
    root = tmp_path / "empty"
    root.mkdir()
    out = tmp_path / "result.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "aggregate_map1.py",
            "--shard-dir", str(root),
            "--output", str(out),
        ],
    )
    code = aggregate_main()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert code == 2
    assert payload["status"] == "INFRASTRUCTURE_BLOCKED"
    assert payload["scientific_decision"] is None
