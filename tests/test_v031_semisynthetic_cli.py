import subprocess
import sys
from pathlib import Path

from scripts import run_v031_semisynthetic as runner


def test_v031_semisynthetic_cli_help_freezes_execution_profile():
    completed = subprocess.run(
        [sys.executable, "scripts/run_v031_semisynthetic.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout
    assert "20" in text
    assert "20260921" in text
    assert "200" in text
    assert "250" in text
    assert "2" in text
    assert "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a" in text
    assert "annual_precipitation.csv" in text


def test_gate_f_builds_one_fresh_python_worker_per_frozen_replicate(tmp_path):
    source_path = tmp_path / "source.csv"
    source_path.write_text("station,lat,long,precipitation\n", encoding="utf-8")

    commands = [
        runner._worker_command(
            replicate=replicate,
            source_path=source_path,
            output_path=tmp_path / f"replicate-{replicate:02d}.json",
            progress_bar=False,
        )
        for replicate in range(runner.FROZEN_REPLICATES)
    ]

    assert len(commands) == runner.FROZEN_REPLICATES == 20
    assert all(command[0] == sys.executable for command in commands)
    assert all(Path(command[1]).name == "run_v031_semisynthetic.py" for command in commands)
    assert all("--_worker-replicate" in command for command in commands)
    assert [
        int(command[command.index("--_worker-replicate") + 1]) for command in commands
    ] == list(range(20))
    assert len({command[command.index("--_worker-output") + 1] for command in commands}) == 20


def test_gate_f_worker_seed_schedule_matches_frozen_in_process_schedule():
    assert [runner._replicate_seed(index) for index in range(4)] == [
        20260921,
        20260958,
        20260995,
        20261032,
    ]
