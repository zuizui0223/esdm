import subprocess
import sys


def test_v031_sbc_cli_help_exposes_frozen_profile():
    completed = subprocess.run(
        [sys.executable, "scripts/run_v031_sbc.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout
    for token in (
        "100",
        "20260918",
        "300",
        "400",
        "2",
        "20000",
        "20260919",
        "49",
    ):
        assert token in text
    assert "not configurable" in text.lower()


def test_v031_sbc_cli_rejects_scientific_profile_overrides():
    completed = subprocess.run(
        [sys.executable, "scripts/run_v031_sbc.py", "--replicates", "2"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "unrecognized arguments" in completed.stderr
