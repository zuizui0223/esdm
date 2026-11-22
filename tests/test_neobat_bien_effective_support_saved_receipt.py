"""Ensure the committed post-hoc BIEN support receipt matches a full frozen replay."""
from pathlib import Path
import math
import json
from numbers import Real

from scripts.neobat_bien_support_reaudit import build_audit, load_receipts


def equivalent(a, b):
    if type(a) is bool or type(b) is bool:
        return type(a) is type(b) and a == b
    if isinstance(a, Real) and isinstance(b, Real):
        return math.isclose(float(a), float(b), rel_tol=1e-13, abs_tol=1e-13)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    return a == b


def test_committed_support_receipt_is_derived_from_preserved_inputs():
    root = Path(__file__).resolve().parents[1]
    panel, receipts, _ = load_receipts(root)
    actual = build_audit(panel, receipts)
    saved = json.loads((root / "docs/replication/neobat" /
                        "bien_fixed10_effective_support_reaudit_20261122.json").read_text(encoding="utf-8"))
    assert equivalent(saved, actual)
    assert saved["interpretation"]["posthoc_reporting_lenses_not_selection_thresholds"]
    assert not saved["interpretation"]["source_independence_from_GBIF_verified"]
