import json

from scripts.aggregate_amap1 import (
    EXPECTED_FIT_COUNT,
    EXPECTED_SHARD_COUNT,
    REPLICATES,
    aggregate_amap1_shards,
    main as aggregate_main,
)
from esdm.validate.amap1_known_truth import make_amap1_worlds
from esdm.validate.amap1_run import amap1_required_fit_plan


def _write_passing(root):
    for world in make_amap1_worlds():
        for replicate in range(REPLICATES):
            payload = {
                "schema": "esdm.amap1.replicate_result.v1",
                "world_id": world.world_id,
                "replicate": replicate,
                "regret": 0.0,
                "detectability_gain": (
                    None
                    if world.detectability_reference is None
                    else 0.012
                ),
                "fits": [
                    {
                        "model_id": model_id,
                        "divergences": 0,
                    }
                    for model_id in amap1_required_fit_plan(world.world_id)
                ],
            }
            path = root / world.world_id / f"{replicate}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )


def test_amap1_aggregate_accepts_complete_frozen_plan(tmp_path):
    _write_passing(tmp_path)
    result = aggregate_amap1_shards(tmp_path)

    assert result["status"] == "PASS"
    assert result["shard_count"] == EXPECTED_SHARD_COUNT == 144
    assert result["fit_count"] == EXPECTED_FIT_COUNT == 384
    assert result["claims"]["LOW_REGRET_MAP_SUPPORTED"] is True
    assert len(result["summaries"]) == 9


def test_amap1_aggregate_rejects_missing_shard(tmp_path):
    _write_passing(tmp_path)
    (tmp_path / "G3_TC" / "15.json").unlink()

    try:
        aggregate_amap1_shards(tmp_path)
    except ValueError as exc:
        assert "missing shards" in str(exc)
    else:
        raise AssertionError("missing AMAP1 shard must fail closed")


def test_amap1_aggregate_rejects_extra_fit(tmp_path):
    _write_passing(tmp_path)
    path = tmp_path / "G1_TX" / "0.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["fits"].append(
        {"model_id": "EXTRA", "divergences": 0}
    )
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        aggregate_amap1_shards(tmp_path)
    except ValueError as exc:
        assert "fit plan drift" in str(exc)
    else:
        raise AssertionError("extra AMAP1 fit must fail closed")


def test_amap1_aggregate_rejects_detectability_leak_into_t0(tmp_path):
    _write_passing(tmp_path)
    path = tmp_path / "G2_T0" / "0.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["detectability_gain"] = 0.5
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        aggregate_amap1_shards(tmp_path)
    except ValueError as exc:
        assert "T0 shard" in str(exc)
    else:
        raise AssertionError("T0 detectability outcome must fail closed")


def test_amap1_aggregate_rejects_missing_detectability_in_field_truth(tmp_path):
    _write_passing(tmp_path)
    path = tmp_path / "G2_TC" / "0.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["detectability_gain"] = None
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        aggregate_amap1_shards(tmp_path)
    except ValueError as exc:
        assert "lacks detectability" in str(exc)
    else:
        raise AssertionError("field truth missing detectability must fail closed")


def test_amap1_aggregate_cli_emits_infrastructure_receipt(tmp_path, monkeypatch):
    root = tmp_path / "empty"
    root.mkdir()
    out = tmp_path / "result.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "aggregate_amap1.py",
            "--shard-dir",
            str(root),
            "--output",
            str(out),
        ],
    )

    code = aggregate_main()
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert code == 2
    assert payload["status"] == "INFRASTRUCTURE_BLOCKED"
    assert payload["scientific_decision"] is None
    assert payload["error_type"] == "ValueError"
