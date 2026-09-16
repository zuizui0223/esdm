import importlib.util
from pathlib import Path
import sys


SCRIPT_PATH = Path("scripts/run_v031_semisynthetic.py")


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("run_v031_semisynthetic", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_f_builds_one_fresh_worker_command_per_frozen_replicate(tmp_path):
    runner = _load_runner_module()
    build = getattr(runner, "_build_worker_command", None)
    assert callable(build), "Gate F must expose a frozen worker-command builder"

    commands = [build(i, tmp_path / f"replicate_{i:02d}.json") for i in range(20)]

    assert len(commands) == 20
    for i, command in enumerate(commands):
        assert command[0] == sys.executable
        assert command[1].endswith("run_v031_semisynthetic_replicate.py")
        assert command[2:] == [
            "--replicate-index",
            str(i),
            "--output",
            str(tmp_path / f"replicate_{i:02d}.json"),
        ]


def test_gate_f_worker_command_does_not_expose_scientific_profile_controls(tmp_path):
    runner = _load_runner_module()
    build = getattr(runner, "_build_worker_command", None)
    assert callable(build), "Gate F must expose a frozen worker-command builder"

    text = " ".join(build(0, tmp_path / "replicate.json"))
    for forbidden in (
        "--num-warmup",
        "--num-samples",
        "--num-chains",
        "--base-seed",
        "--credible-mass",
        "--source",
    ):
        assert forbidden not in text
