"""Synthetic, original-outcome-blind checks of E7-C direct camera-year analysis."""
from __future__ import annotations

from collections import Counter, defaultdict
import math
from pathlib import Path

import pytest

from scripts.e7_direct_camera_year_diel import (
    EXPECTED_PANEL, MIN_SITES, MIN_SITE_YEARS, MIN_SOURCE_SEASONS,
    collect_within_cell_diel_changes, pair_result, summarize, triple_closure,
)

ROOT = Path(__file__).resolve().parents[1]


def _example(*, sites=6, years=(2015, 2016), missing=None, flat=False):
    counts, folder_support = Counter(), defaultdict(set)
    species = ("buffalo", "giraffe", "wildebeest")
    for i in range(sites):
        loc = f"site{i}"
        for water in years:
            for phase in ("wet", "dry"):
                folder_support[(loc,water,phase)].update((1,2,3))
                for j,name in enumerate(species):
                    # Distinct species seasonal diel responses; alternatively
                    # different abundance scaling with identical diel profile.
                    if flat:
                        n,day = (8,4) if phase=="wet" else (24,12)
                    else:
                        n,day = (8+2*j,4+2*j) if phase=="wet" else (4+2*j,8+2*j)
                    if missing == (loc,water,name,phase):
                        day=0
                    counts[(loc,water,phase,name,"night")] = n
                    counts[(loc,water,phase,name,"midday")] = day
    return counts, folder_support


def test_local_species_delta_and_triangle_identity_close_on_exact_same_cell():
    counts,folders = _example()
    matched = collect_within_cell_diel_changes(counts,folders,EXPECTED_PANEL)
    assert len(matched) == 12
    for rec in matched.values():
        assert set(rec["changes"]) == {"buffalo","giraffe","wildebeest"}
    t = triple_closure(matched)
    assert t["complete_three_taxon_site_years"] == 12
    assert t["triple_site_year_identity_checks"] == 12
    assert t["maximum_absolute_log_cycle_gap"] < 1e-12
    result = summarize(matched,EXPECTED_PANEL)
    assert result["possible_pairs"] == 66
    assert result["estimable_pairs"] == 3
    bp = next(p for p in result["all_66_pairs_including_support_refusals"]
              if (p["species_1"],p["species_2"])==("buffalo","giraffe"))
    assert bp["status"]=="DESCRIPTIVE_DIRECT_CELL_ESTIMABLE"
    assert bp["eligible_matched_site_years"]==12
    assert bp["eligible_distinct_cameras"]==6
    assert bp["original_source_folders"]==3
    assert bp["leave_one_camera"]["all_computable"] is True
    assert math.isclose(bp["median_local_log_dry_wet_relative_diel_change"],
                        (math.log(4/8)-math.log(8/4)) -
                        (math.log(6/10)-math.log(10/6)),rel_tol=1e-12)


def test_decline_when_sites_or_site_years_insufficient():
    x,f = _example(sites=4,years=(2015,2016))
    z=collect_within_cell_diel_changes(x,f,EXPECTED_PANEL)
    assert len(z)==8
    r=pair_result(z,"buffalo","giraffe")
    assert (r["eligible_matched_site_years"],r["eligible_distinct_cameras"])==(8,4)
    assert r["status"]=="INSUFFICIENT_DIRECT_CELL_SUPPORT"
    assert r["median_local_log_dry_wet_relative_diel_change"] is None
    assert not r["leave_one_camera"]["sign_stable"]


def test_missing_one_diel_bin_excludes_only_affected_siteyear_and_species():
    x,f = _example(missing=("site0",2015,"giraffe","wet"))
    z=collect_within_cell_diel_changes(x,f,EXPECTED_PANEL)
    assert "giraffe" not in z[("site0",2015)]["changes"]
    assert "buffalo" in z[("site0",2015)]["changes"]
    result = pair_result(z,"buffalo","giraffe")
    assert result["eligible_matched_site_years"]==11
    assert result["status"]=="DESCRIPTIVE_DIRECT_CELL_ESTIMABLE"


def test_seasonal_abundance_scaling_does_not_create_false_local_diel_shift():
    x,f=_example(flat=True)
    z=collect_within_cell_diel_changes(x,f,EXPECTED_PANEL)
    for rec in z.values():
        assert all(abs(value)<1e-12 for value in rec["changes"].values())
    q=pair_result(z,"buffalo","wildebeest")
    assert q["status"]=="DESCRIPTIVE_DIRECT_CELL_ESTIMABLE"
    assert q["median_local_log_dry_wet_relative_diel_change"]==0
    assert q["fraction_local_changes_positive"]==0
    assert not q["leave_one_camera"]["sign_stable"]
    assert triple_closure(z)["maximum_absolute_log_cycle_gap"]==0


def test_source_panel_and_guardrails_are_fixed_before_field_open():
    assert len(EXPECTED_PANEL)==12
    assert (MIN_SITES,MIN_SITE_YEARS,MIN_SOURCE_SEASONS)==(5,10,3)
    source=(ROOT/"scripts"/"e7_direct_camera_year_diel.py").read_text(encoding="utf-8")
    assert "source_qc_agreement" in source
    assert "source file sha256 mismatch" in source
    assert "frozen E7 result JSON sha256 changed" in source
    for forbidden in ("num_warmup", "num_samples", "numpyro", "estimated_NDVI"):
        assert forbidden not in source
