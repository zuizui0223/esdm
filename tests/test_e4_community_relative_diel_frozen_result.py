"""Guard the independently frozen E4 community-relative diel output.

Tests only source-receipt aggregates and the new postresult result receipt.
No primary biological archive, MCMC or geographical outcome is reopened.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "docs" / "replication"


def read(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_site_matched_output_is_pinned_to_original_capture_and_one_successful_run():
    r = read("E4_COMMUNITY_RELATIVE_DIEL_RESULT_RECEIPT.json")
    p = r["provenance"]
    assert r["status"] == "POSTRESULT_OUTCOME_SELECTED_COMMUNITY_RELATIVE_DIEL_AUDIT"
    assert p["workflow_run_id"] == 39203272457
    assert p["workflow_run_attempt"] == 1
    assert p["workflow_conclusion"] == "success"
    assert p["audit_artifact_id"] == 12164721283
    assert p["audit_artifact_zip_digest"] == (
        "sha256:ec2d6e77e69a9926148200851430d2033ebc70530ff40e4c6080f3542294971a"
    )
    assert p["original_source_capture_run_id"] == 36369531079
    assert p["original_mica_archive_sha256"] == (
        "8346f3fe467a201525d6bedd4ebd6e2078457ee8bb778501d41d55ace7d962c9"
    )


def test_exact_raw_observation_odds_agree_with_previously_frozen_eight_taxa():
    r = read("E4_COMMUNITY_RELATIVE_DIEL_RESULT_RECEIPT.json")
    prior = read("E4_MICA_POSTRESULT_CROSS_TAXON_DIEL_SUPPLEMENT.json")
    taxa = {row["scientificName"]: row for row in prior["taxa"]}
    rat = taxa["Rattus norvegicus"]
    mus = taxa["Ondatra zibethicus"]
    observed = r["pooled_observation_result"]
    for cohort, field in [("training", "training"), ("heldout_D", "heldout_D")]:
        odds = (
            rat[cohort + "_night_events"] * mus[cohort + "_day_events"]
            / (rat[cohort + "_day_events"] * mus[cohort + "_night_events"])
        )
        assert math.isclose(observed[field + "_rat_over_muskrat_diel_odds"], odds, rel_tol=1e-12)
    assert math.isclose(
        observed["heldout_over_training_ratio"],
        observed["heldout_D_rat_over_muskrat_diel_odds"]
        / observed["training_rat_over_muskrat_diel_odds"],
        rel_tol=1e-12,
    )
    assert math.isclose(observed["heldout_over_training_ratio"], 9.598372737319233, rel_tol=1e-12)


def test_shared_site_reversal_is_separated_under_all_one_site_deletions():
    r = read("E4_COMMUNITY_RELATIVE_DIEL_RESULT_RECEIPT.json")
    sites = r["site_stratified"]
    west, east = sites["training"], sites["heldout_D"]
    assert (west["all_physical_locations"], east["all_physical_locations"]) == (27, 8)
    assert (west["informative_sites"], east["informative_sites"]) == (20, 8)
    assert (west["sites_with_both_species"], east["sites_with_both_species"]) == (20, 8)
    assert (west["loo_valid_contrasts"], east["loo_valid_contrasts"]) == (20, 8)
    assert west["loo_max"] < 1 < east["loo_min"]
    assert west["recorded_muskrat_events_in_shared_sites"] == 1337
    assert east["recorded_muskrat_events_in_shared_sites"] == 5091
    assert east["recorded_rat_events_in_shared_sites"] == 1772
    assert 0 < west["mh_rat_over_muskrat_diel_odds"] < 1
    assert east["mh_rat_over_muskrat_diel_odds"] > 1
    assert math.isclose(
        sites["ratio_of_site_stratified_MH_odds"],
        east["mh_rat_over_muskrat_diel_odds"]
        / west["mh_rat_over_muskrat_diel_odds"],
        rel_tol=1e-12,
    )
    assert math.isclose(sites["ratio_of_site_stratified_MH_odds"], 8.706068486504277)
    assert sites["qualitative_decision"] == "SITE_MATCHED_DESCRIPTIVE_ESTIMABLE_NO_CAUSAL_ATTRIBUTION"


def test_ecological_inference_firewalls_and_documentation_survive_merge():
    r = read("E4_COMMUNITY_RELATIVE_DIEL_RESULT_RECEIPT.json")
    boundary = r["integrity_and_claims"]
    assert r["fixed_design"]["selection_informed_by_previously_observed_species_directions"] is True
    assert boundary["new_fit"] is False
    assert boundary["E4_frozen_result_changed"] is False
    assert boundary["E5_original_G4_passed"] is False
    assert boundary["E5_original_qualified_candidates"] == 0
    assert boundary["independently_identified_true_passage_or_detection"] is False
    assert boundary["confirmatory_inference"] is False
    assert boundary["raw_animal_rows_exported"] is False
    assert boundary["individual_site_identifiers_exported"] is False
    note = (DATA / "E4_COMMUNITY_RELATIVE_DIEL_RESEARCH_NOTE.md").read_text(encoding="utf-8")
    assert "8.70607" in note
    assert "site" in note.lower()
    assert "not a preregistered" in note.lower()
    assert "not a new e5" in note.lower()
