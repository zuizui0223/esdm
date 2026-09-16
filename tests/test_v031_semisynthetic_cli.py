import subprocess
import sys


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
