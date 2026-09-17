import subprocess
import sys


def test_v031_knockout_cli_help_freezes_profile():
    completed = subprocess.run(
        [sys.executable, "scripts/run_v031_knockout.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout
    for token in ("100", "20260920", "250", "300", "2", "0.90"):
        assert token in text
    assert "not configurable" in text.lower()


def test_v031_knockout_cli_rejects_profile_overrides():
    completed = subprocess.run(
        [sys.executable, "scripts/run_v031_knockout.py", "--replicates", "2"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "unrecognized arguments" in completed.stderr
