"""Synthetic-only mathematical correctness for post-result S14-FM.

Never opens source animal records or treats null states as independent parks.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
import math
from pathlib import Path
import random
from tempfile import TemporaryDirectory

import pytest

from scripts.safari14_fixed_margins_camera_null import (
    BURNIN_PER_CAMERA, BETWEEN_PER_CAMERA, COMPARE_DRAWS,
    MIN_POSITIVE_PAIRED_DRAWS, NULL_SEED, ORIGINAL_JSON_SHA256,
    beta_components, camera_index_draws, curveball, digest, label_set,
    margin_signature, original_camera_draws, per_partition_null,
    summary_for_group, verify_original_reconstruction,
)
from scripts.safari14_spatial_beta import DISCOVERY, VALIDATION, PROJECTS


def test_original_fixed_margin_preserving_curveball_trade():
    rows = [
        {"lion","zebra","buffalo"}, {"wildebeest","lion","giraffe"},
        {"elephant","wildebeest"}, {"zebra","elephant","giraffe"},
        set(), {"buffalo","giraffe","zebra"},
    ]
    row_margins,cols=margin_signature(rows)
    rng=random.Random(29)
    accepted=sum(curveball(rows,rng) for _ in range(2000))
    assert accepted>100
    assert margin_signature(rows)==(row_margins,cols)
    assert rows[-2]==set()
    assert all(isinstance(x,set) for x in rows)


def test_curveball_must_leave_subset_and_identical_camera_sets_unchanged():
    rows=[{"a","b"},{"a","b"},{"a"},set()]
    expected=margin_signature(rows)
    assert sum(curveball(rows,random.Random(i)) for i in range(50))==0
    assert margin_signature(rows)==expected


def _camera_matrix(*, stable=False):
    out={}
    for park in PROJECTS:
        cams=[]
        for i in range(12):
            # Equal nominal per-camera row richness; park-specific
            # species replacement if not stationary.
            if stable:
                labels={"zebra","wildebeest"}
            else:
                labels={"zebra",f"park_{park}"}
            cams.append((f"camera_{i:02d}",labels))
        out[park]=cams
    return out


def test_original_subsample_indices_match_original_tuple_sample_rng():
    cameras=_camera_matrix()
    planned=camera_index_draws(cameras,draws=25)
    rng=random.Random(20261111)
    for selection in planned:
        for park in PROJECTS:
            by_indices=[cameras[park][i] for i in selection[park]]
            by_original=rng.sample(cameras[park],10)
            assert by_indices==by_original


def test_nonrandom_observed_park_labels_can_exceed_margins_constrained_null():
    cameras=_camera_matrix()
    selections=camera_index_draws(cameras,draws=25)
    observed=original_camera_draws(cameras,selections)
    discovery=per_partition_null(cameras,DISCOVERY,selections,
        observed["draws"]["discovery"],seed=20261114,burn=20,between=12)
    validation=per_partition_null(cameras,VALIDATION,selections,
        observed["draws"]["validation"],seed=20261115,burn=20,between=12)
    for r,expected in ((discovery,7*12),(validation,5*12)):
        assert r["source_camera_rows"]==expected
        assert r["all_camera_row_sums_preserved"] is True
        assert r["all_partition_species_camera_incidence_marginals_preserved"] is True
        assert r["paired_draws"]==25
        assert r["fully_eligible_paired_draws"]==25
        assert r["observed_median_beta_sim"]==.5
        assert r["null_median_beta_sim"]<.5
        assert r["observed_gt_null_draw_count"]>=20
        assert r["total_between_draw_accepted_trades"]>0
        assert len(r["all_within_partition_park_pair_summaries"])==(
            expected//12*(expected//12-1)//2
        )


def test_identical_global_camera_label_sets_give_no_excess_or_mixing():
    cameras=_camera_matrix(stable=True)
    selections=camera_index_draws(cameras,draws=15)
    observed=original_camera_draws(cameras,selections)
    result=per_partition_null(cameras,DISCOVERY,selections,
        observed["draws"]["discovery"],seed=20261114,burn=5,between=5)
    assert result["fully_eligible_paired_draws"]==15
    assert result["observed_median_beta_sim"]==0
    assert result["null_median_beta_sim"]==0
    assert result["median_paired_beta_sim_excess"]==0
    assert result["observed_gt_null_draw_count"]==0
    assert result["initial_burnin_accepted_trades"]==0
    assert result["total_between_draw_accepted_trades"]==0


def test_baselga_partition_preserved_and_invalid_source_rejected():
    assert beta_components({"a","b"},{"a","c"}) == (.5,.5,0)
    assert beta_components({"a","b"},{"a"}) == (1/3,0,1/3)
    assert summary_for_group({("X","Y"):None})["pair_count"]==0
    assert label_set([{"lion"},{"lion"},{"zebra"}],[0,1,2])=={"lion"}
    assert (BURNIN_PER_CAMERA,BETWEEN_PER_CAMERA,COMPARE_DRAWS,
            MIN_POSITIVE_PAIRED_DRAWS,NULL_SEED)==(30,15,500,475,20261114)
    assert ORIGINAL_JSON_SHA256=="f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7"
    with pytest.raises(ValueError,match="exact reconstruction requires"):
        verify_original_reconstruction({}, {},draws=20)
