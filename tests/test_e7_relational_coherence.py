"""Regression and synthetic tests for E7 frozen post-result relational audit."""
from __future__ import annotations

import math
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from scripts import e7_relational_coherence as audit

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "docs" / "replication" / "E7_RELATIONAL_PAIRWISE_66.csv"


def test_source_table_is_complete_and_sha_pinned():
    rows = audit.load_pinned_pair_table(TABLE)
    assert len(rows) == 66
    assert sum(r["discovery_status"] == "DESCRIPTIVE_ESTIMABLE" for r in rows) == 54
    assert sum(r["validation_status"] == "DESCRIPTIVE_ESTIMABLE" for r in rows) == 50
    assert audit.sha256_file(TABLE) == audit.PAIR_CSV_SHA256


def test_original_frozen_result_coherence_and_holdout_skill():
    r = audit.analyze(audit.load_pinned_pair_table(TABLE), check_expected=True)
    assert r["support"]["shared_estimated_pairs"] == 46
    assert r["support"]["taxa_in_connected_shared_pair_graph"] == 11
    assert r["support"]["taxa_without_any_shared_eligible_edge"] == ["reedbuck"]
    assert math.isclose(r["discovery"]["energy_explained_relative_zero"], 0.5512442064061597, abs_tol=1e-11)
    assert math.isclose(r["validation"]["energy_explained_relative_zero"], 0.37443908947904125, abs_tol=1e-11)
    assert r["discovery"]["complete_taxon_triples"] == 104
    assert r["validation"]["complete_taxon_triples"] == 104
    assert math.isclose(r["discovery"]["median_absolute_log_cycle_gap"], 0.8510528222801812, abs_tol=1e-12)
    assert math.isclose(r["validation"]["median_absolute_log_cycle_gap"], 0.7080204284474858, abs_tol=1e-12)
    assert math.isclose(r["out_of_period"]["discovery_species_gradient_on_validation_pair_edges_skill_vs_zero"],
                        -0.7552148994346888, abs_tol=1e-11)
    assert r["out_of_period"]["pair_shift_sign_agreement"] == 23
    assert r["ecological_boundary"]["triangle_inconsistency_does_not_prove_interspecific_interaction"] is True
    assert r["ecological_boundary"]["original_E5_G4_passed"] is False


def test_exact_species_gradient_obeys_triangle_identity():
    taxa = ["A","B","C","D"]
    beta = {"A":-0.75,"B":-0.25,"C":0.5,"D":0.5}
    edges = [(a,b) for i,a in enumerate(taxa) for b in taxa[i+1:]]
    delta = [beta[a]-beta[b] for a,b in edges]
    fit = audit._gradient_fit(edges,delta,taxa)
    triangles = audit._cycles(edges,delta,taxa)
    assert math.isclose(fit["energy_explained_relative_zero"],1.0,abs_tol=1e-13)
    assert fit["RMSE_log_dry_wet"] < 1e-12
    assert triangles["complete_taxon_triples"] == 4
    assert triangles["median_absolute_log_cycle_gap"] < 1e-12


def test_nontransitive_pairwise_effects_leave_cycle_gap():
    taxa = ["A","B","C"]
    edges = [("A","B"),("A","C"),("B","C")]
    values = [1.,3.,1.]
    fit = audit._gradient_fit(edges,values,taxa)
    cycle = audit._cycles(edges,values,taxa)
    assert fit["energy_explained_relative_zero"] < 1.0
    assert math.isclose(cycle["median_absolute_log_cycle_gap"], 1.0)


def test_disconnected_support_is_not_assigned_species_scores():
    with pytest.raises(ValueError,match="disconnected"):
        audit._gradient_fit([("A","B"),("C","D")],[1.,-1.],["A","B","C","D"])


def test_modified_aggregate_file_is_rejected_without_reanalysis():
    with TemporaryDirectory() as directory:
        out=Path(directory)/"tampered.csv"
        out.write_bytes(TABLE.read_bytes().replace(b"buffalo",b"BUFFALO",1))
        with pytest.raises(ValueError,match="SHA256"):
            audit.load_pinned_pair_table(out)
