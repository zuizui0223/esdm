"""Source-free workflow path contract: never confuse original stop and corrected receipt."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


class CorrectedWorldClimWorkflowPaths(unittest.TestCase):
    def test_same_corrected_output_is_archived_committed_and_gated(self):
        root = Path(__file__).resolve().parents[1]
        path = root / ".github/workflows/neobat-worldclim-corrected-source-preflight.yml"
        text = path.read_text(encoding="utf-8")
        prefix = "docs/replication/neobat/worldclim_bio1_bio12_corrected_source_preflight"
        source_json = prefix + ".json"
        exit_code = prefix + "_exit_code.txt"

        # Test the actual output and the downstream archival/commit/gate
        # paths without depending on unpinned YAML parsing packages.
        self.assertIn("--out " + source_json, text)
        self.assertIn('echo "$status" > ' + exit_code, text)
        self.assertIn("if-no-files-found: error", text)
        self.assertIn("git add " + prefix + "*", text)
        self.assertIn('test "$(cat ' + exit_code + ')" = "0"', text)
        self.assertGreaterEqual(text.count(source_json), 2)
        self.assertGreaterEqual(text.count(exit_code), 3)

        # An obsolete STOP receipt may coexist on disk but must never
        # satisfy the corrected scientific source qualification.
        self.assertNotIn(
            "docs/replication/neobat/worldclim_bio1_bio12_source_preflight.json",
            text,
        )
        self.assertNotIn(
            "docs/replication/neobat/worldclim_bio1_bio12_source_preflight_exit_code.txt",
            text,
        )


if __name__ == "__main__":
    unittest.main()
