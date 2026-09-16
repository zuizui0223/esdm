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
        "default: 100",
        "default: 20260918",
        "default: 300",
        "default: 400",
        "default: 2",
        "default: 20000",
        "default: 20260919",
        "default: 49",
    ):
        assert token in text
