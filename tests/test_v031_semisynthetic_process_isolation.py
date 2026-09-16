from pathlib import Path
import sys

from scripts import run_v031_semisynthetic as runner


def test_gate_f_worker_command_does_not_expose_scientific_profile_controls(tmp_path):
    source_path = tmp_path / "source.csv"
    output_path = tmp_path / "replicate.json"

    command = runner._worker_command(
        replicate=0,
        source_path=source_path,
        output_path=output_path,
        progress_bar=False,
    )

    assert command[0] == sys.executable
    assert Path(command[1]).name == "run_v031_semisynthetic.py"
    assert command[command.index("--_worker-replicate") + 1] == "0"
    assert command[command.index("--_worker-source") + 1] == str(source_path)
    assert command[command.index("--_worker-output") + 1] == str(output_path)

    text = " ".join(command)
    for forbidden in (
        "--num-warmup",
        "--num-samples",
        "--num-chains",
        "--base-seed",
        "--credible-mass",
    ):
        assert forbidden not in text
