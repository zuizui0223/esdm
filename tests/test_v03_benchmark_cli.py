import subprocess
import sys
from pathlib import Path


def test_v03_known_truth_cli_exposes_frozen_defaults_without_running_fit():
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_v03_known_truth.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--replicates" in result.stdout
    assert "default: 100" in result.stdout
    assert "--base-seed" in result.stdout
    assert "default: 20260916" in result.stdout
    assert "--output" in result.stdout
