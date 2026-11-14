"""Illustrative structural null guardrails for frozen S14 aggregate only."""
from __future__ import annotations

import json
import math
from pathlib import Path
import random
from tempfile import TemporaryDirectory

import pytest

from scripts.safari14_structural_null_sensitivity import (
    DRAWS, FREQUENCY_EXPONENTS, GROUPS, PINNED_INPUT_SHA256,
    SEED, analyze, beta_components, draw_without_replacement, observed_input
)


def _source_fixture():
    parks = {p: {"median_10_camera_detected_species":rich}
             for p,rich in zip(GROUPS["discovery"] + GROUPS["validation"],
                 (17,10,19.5,9,7,15,6,15,13,15,20,15),strict=True)}
    return {
        "source":{"original_zip_sha256":"2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1"},
        "quality":{
            "matched_wild_mammal_annotation_rows_by_label":{
                f"taxon{i:02d}":(i+1)**3 for i in range(38)
            }
        },
        "results":{
            "eligible_projects":list(GROUPS["discovery"]+GROUPS["validation"]),
            "predeclared_turnover_dominant_in_both_splits":True,
            "project_summary":parks,
            "beta_summary_by_project_partition":{
                g:{"valid_resampling_draws":500,"turnover_dominant_draws":500,
                   "median_pair_sim": .4 if g=="discovery" else .35,
                   "median_pair_sne": .12 if g=="discovery" else .06}
                for g in GROUPS
            }
        }
    }


def test_baselga_pair_partition_and_no_empty_sets():
    assert beta_components({"a","b"},{"a","c"}) == (.5,.5,0.)
    assert beta_components({"a","b"},{"a"}) == (1/3,0.,1/3)
    assert beta_components({"a"},{"b"}) == (1.,1.,0.)
    with pytest.raises(ValueError,match="nonempty"):
        beta_components(set(),{"a"})


def test_weighted_without_replacement_respects_seed_size_and_weight_validation():
    left=draw_without_replacement([1]*38,17,random.Random(22))
    right=draw_without_replacement([1]*38,17,random.Random(22))
    assert left==right and len(left)==17
    assert len(draw_without_replacement([1e-3]*18+[10]*20,24,random.Random(22)))==24
    with pytest.raises(ValueError,match="richness"):
        draw_without_replacement([1]*38,39,random.Random(22))
    with pytest.raises(ValueError,match="weights"):
        draw_without_replacement([1,-1,2],1,random.Random(22))


def test_positive_turnover_can_arise_under_park_independent_uniform_sampling():
    v=analyze(_source_fixture(),draws=40,seed=2)
    assert len(v["null_scenarios"])==3
    uniform=v["null_scenarios"]["0.0"]
    assert uniform["discovery"]["null_turnover_dominance_fraction"]>0.9
    assert uniform["validation"]["null_turnover_dominance_fraction"]>0.9
    assert v["settings"]["park_richness"]["ENO"]==20
    assert v["settings"]["label_pool_size"]==38
    assert v["interpretation"]["nonrandom_assembly_proven"] is False
    assert v["source"]["biological_source_zip_reopened"] is False


def test_an_illustrative_frequency_weight_change_moves_expected_turnover():
    result=analyze(_source_fixture(),draws=40,seed=1)
    u=result["null_scenarios"]["0.0"]
    weighted=result["null_scenarios"]["1.0"]
    for group in GROUPS:
        assert u[group]["median_null_beta_sim"]>weighted[group]["median_null_beta_sim"]
        assert u[group]["median_null_beta_sne"]<weighted[group]["median_null_beta_sne"]
    assert result["settings"]["null_draws_are_illustrative_not_field_replicates"]
    assert result["interpretation"]["formal_null_significance_or_confidence_intervals"] is False
    assert result["interpretation"]["original_E4_E5_E7_E7C_S14_findings_modified"] is False


def test_original_s14_result_must_be_hash_verified_before_use():
    assert PINNED_INPUT_SHA256=="f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7"
    assert DRAWS==500
    assert SEED==20261114
    assert FREQUENCY_EXPONENTS==(0.0,0.5,1.0)
    with TemporaryDirectory() as tmp:
        path=Path(tmp)/"fake_result.json"
        path.write_text(json.dumps(_source_fixture()),encoding="utf-8")
        with pytest.raises(ValueError,match="SHA256"):
            observed_input(path)
