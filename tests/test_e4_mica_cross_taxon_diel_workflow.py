from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e4-mica-cross-taxon-diel.yml"


def test_cross_taxon_diel_workflow_is_postresult_artifact_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "run-id: 36369531079" in text
    assert "E2_MICA_TEMPORAL_INTEGRITY_RESULT.json" in text
    assert "audit_e4_mica_cross_taxon_diel.py" in text
    for forbidden in (
        "fit_numpyro",
        "fit_e4_mica_sparse",
        "num_warmup",
        "num_samples",
        "workflow_dispatch",
        "Laplace",
        "INLA",
    ):
        assert forbidden not in text
