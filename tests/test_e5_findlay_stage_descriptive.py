from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path

import pytest

from scripts.run_e5_findlay_pass_stage_descriptive import (
    git_blob_sha, distance_bin, count_records, summarize
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs"/"replication"/"E5_FINDLAY_STAGE_DESCRIPTIVE_CONTRACT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-findlay-stage-descriptive-once.yml"


def _fixture(*, mismatch=False):
    v=json.loads(CONTRACT.read_text(encoding="utf-8"))
    trigger=io.StringIO()
    register=io.StringIO()
    th=["SPECIES","ORIENT","DIST","TRIGGER","CT.POS"]
    rh=["SPECIES","ORIENT","DIST","TRIGGER","CAPTURE","CT.POS"]
    tw=csv.writer(trigger);tw.writerow(th)
    rw=csv.writer(register);rw.writerow(rh)
    for species in ("BADGER","FOX"):
        for dist,ntrigger in ((0.5,10),(2.0,8),(4.0,6)):
            for k in range(12):
                t=int(k<ntrigger)
                tw.writerow([species,"L",dist,t,"camera1"])
                if t and not (mismatch and species=="BADGER" and dist==0.5 and k==0):
                    capture = 1 if dist==4.0 or (k%2==0) else 0
                    rw.writerow([species,"L",dist,1,capture,"camera1"])
    raw=[trigger.getvalue().encode(),register.getvalue().encode()]
    for spec,data in zip(v["source"]["files"],raw):
        spec["sha"]=git_blob_sha(data)
        spec["bytes"]=len(data)
    return v,{spec["name"]:data for spec,data in zip(v["source"]["files"],raw)}


def test_distance_bin_frozen_edges():
    assert distance_bin("1")=="near_le_1m"
    assert distance_bin("1.0001")=="mid_1_to_3m"
    assert distance_bin("3")=="mid_1_to_3m"
    assert distance_bin("3.0001")=="far_gt_3m"
    assert distance_bin("nan") is None
    assert distance_bin("0") is None


def test_separate_passage_denominators_and_stage_compensation():
    c,data=_fixture()
    out=summarize(c,data)
    assert out["status"]=="RETROSPECTIVE_DESCRIPTIVE_COMPLETED_NO_E5_GATE_PROMOTION"
    assert len(out["stage_cells"])==6
    cells={(x["species"],x["distance_bin"]):x for x in out["stage_cells"]}
    near=cells[("BADGER","near_le_1m")]
    far=cells[("BADGER","far_gt_3m")]
    assert near["cctv_reference_passes"]==12
    assert near["triggered_reference_passes"]==10
    assert near["registration_eligible_triggered_rows"]==10
    assert near["registered_images"]==5
    assert near["p_composite_given_pass"]==pytest.approx(5/12)
    assert far["p_composite_given_pass"]==pytest.approx(6/12)
    result=out["primary_far_vs_near_by_species"]["BADGER"]
    assert result["status"]=="DESCRIPTIVE_OPPOSING_STAGES"
    assert result["log_far_vs_near_trigger"]<0
    assert result["log_far_vs_near_registration"]>0
    assert 0<result["compensation_index"]<=1
    assert out["boundary"]["original_E5_G4_passed"] is False


def test_mismatched_study_stage_cohort_disallows_composite():
    c,data=_fixture(mismatch=True)
    out=summarize(c,data)
    near=next(x for x in out["stage_cells"]
        if x["species"]=="BADGER" and x["distance_bin"]=="near_le_1m")
    assert near["triggered_cohorts_align"] is False
    assert near["p_composite_given_pass"] is None
    assert out["primary_far_vs_near_by_species"]["BADGER"]["status"]=="COHORT_NONCOMPARABLE"


def test_reject_source_byte_or_pin_drift():
    c,data=_fixture()
    c["source"]["files"][0]["sha"]="0"*40
    with pytest.raises(ValueError,match="blob mismatch"):
        summarize(c,data)


def test_frozen_retrospective_boundary():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert c["status"]=="FROZEN_RETROSPECTIVE_PUBLISHED_DIRECTION_EXPOSED_NOT_AUTHORIZED"
    assert c["cohort_rules"]["orientation"]=="L"
    assert c["cohort_rules"]["minimum_reference_passes_per_bin"]==10
    assert c["cohort_rules"]["minimum_triggered_passes_per_bin"]==5
    assert c["frozen_estimands"]["confidence_intervals_authorized"] is False
    assert c["firewall"]["published_qualitative_direction_already_known"] is True
    assert c["firewall"]["original_E5_qualified_candidates"]==0
    assert c["firewall"]["no_reanalysis_of_frozen_wildpig_or_rhode"] is True


def test_workflow_one_shot_only_and_no_raw_output():
    text=WORKFLOW.read_text(encoding="utf-8")
    assert "e5/findlay-stage-descriptive-once-v1" in text
    assert "E5_FINDLAY_STAGE_DESCRIPTIVE_AUTHORIZED.json" in text
    assert "workflow_dispatch" not in text
    assert "pure marker" in text
    assert "run_e5_findlay_pass_stage_descriptive.py" in text
