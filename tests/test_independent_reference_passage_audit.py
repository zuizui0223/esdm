"""Strict new independent-reference data contract tests (synthetic data ONLY)."""
from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.independent_reference_passage_audit import (
    REQUIRED_EFFORT, REQUIRED_PASSAGES, audit
)


def _write(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=sorted(header))
        writer.writeheader()
        writer.writerows(rows)


def _generate(folder):
    effort=folder/"effort.csv"
    references=folder/"reference_passages.csv"
    effort_rows=[]
    pass_rows=[]
    phase_def={"A":"2026-06-20","B":"2026-07-20"}
    index=0
    # Independent passage rate has NO night/day change between phases.
    # Only camera yield changes in phase B: night 2/10, midday 8/10.
    for phase, when in phase_def.items():
        for clock, hour in (("night","22"),("midday","12")):
            effort_rows.append({
                "site_id":"site_1","phase":phase,"clock_bin":clock,
                "camera_operational_minutes":600,
                "independent_reference_minutes":600,
                "reference_sampling_scheme":"continuous_reference",
            })
            observed = (5 if phase=="A" else (2 if clock=="night" else 8))
            for j in range(10):
                index+=1
                detected=j<observed
                pass_rows.append({
                    "independent_passage_id":f"reference_{index:04d}",
                    "site_id":"site_1","phase":phase,"clock_bin":clock,
                    "species":"Vulpes vulpes",
                    "reference_source_id":"independent_video_1",
                    "reference_timestamp":f"{when}T{hour}:15:00+09:00",
                    "camera_triggered":"1" if detected else "0",
                    "species_registered":"1" if detected else "0",
                    "camera_event_id":f"camera_{index:04d}" if detected else "",
                })
    _write(effort, REQUIRED_EFFORT, effort_rows)
    _write(references, REQUIRED_PASSAGES, pass_rows)
    return effort, references, effort_rows, pass_rows


def test_independent_reference_shows_camera_artifact_without_animal_diel_change():
    with TemporaryDirectory() as temp:
        e,p,_,_= _generate(Path(temp))
        result=audit(e,p)
        assert result["source"]["independent_passage_rows"]==40
        assert len(result["strata"])==4
        bins={(s["phase"],s["clock_bin"]):s["species_calibration"][0]
              for s in result["strata"]}
        for phase in ("A","B"):
            assert bins[(phase,"night")]["independent_reference_passages"]==10
            assert bins[(phase,"midday")]["independent_reference_passages"]==10
            assert bins[(phase,"night")]["independent_passage_rate_per_reference_hour"] == 1.0
            assert bins[(phase,"midday")]["independent_passage_rate_per_reference_hour"] == 1.0
        assert bins[("A","night")]["effective_detection_given_known_passage"] == .5
        assert bins[("A","midday")]["effective_detection_given_known_passage"] == .5
        assert bins[("B","night")]["effective_detection_given_known_passage"] == .2
        assert bins[("B","midday")]["effective_detection_given_known_passage"] == .8
        assert result["limits"]["original_E5_G4_passed"] is False


@pytest.mark.parametrize("mutation,message",[
    ("duplicate_passage","duplicate independent"),
    ("registered_without_trigger","registration cannot occur"),
    ("missing_trigger_status","binary"),
    ("wrong_clock","contradicts timestamp"),
    ("duplicate_camera_event","matched to multiple"),
    ("timestamp_without_timezone","explicit timezone"),
    ("passage_missing_effort","lacks independent effort"),
    ("reference_equals_camera_event","reused as focal camera"),
])
def test_unsafe_crosswalk_or_missingness_refused(mutation,message):
    with TemporaryDirectory() as temp:
        root=Path(temp)
        e,p,er,pr=_generate(root)
        if mutation=="duplicate_passage":
            pr[1]["independent_passage_id"]=pr[0]["independent_passage_id"]
        elif mutation=="registered_without_trigger":
            pr[9]["species_registered"]="1"
        elif mutation=="missing_trigger_status":
            pr[0]["camera_triggered"]=""
        elif mutation=="wrong_clock":
            pr[0]["clock_bin"]="midday"
        elif mutation=="duplicate_camera_event":
            pr[1]["camera_event_id"]=pr[0]["camera_event_id"]
        elif mutation=="timestamp_without_timezone":
            pr[0]["reference_timestamp"]="2026-06-20T22:15:00"
        elif mutation=="passage_missing_effort":
            pr[0]["site_id"]="other_site"
        elif mutation=="reference_equals_camera_event":
            pr[0]["independent_passage_id"]=pr[0]["camera_event_id"]
        _write(p,REQUIRED_PASSAGES,pr)
        with pytest.raises(ValueError,match=message):
            audit(e,p)


@pytest.mark.parametrize("mutation,message",[
    ("trigger_selected_reference","cannot be selected by camera trigger"),
    ("duplicate_effort","duplicate effort stratum"),
    ("reference_exceeds_camera","exceeds camera"),
    ("zero_reference_duration","finite and positive")
])
def test_invalid_denominators_refused(mutation,message):
    with TemporaryDirectory() as temp:
        root=Path(temp)
        e,p,er,pr=_generate(root)
        if mutation=="trigger_selected_reference":
            er[0]["reference_sampling_scheme"]="camera_trigger_selected"
        elif mutation=="duplicate_effort":
            er.append(dict(er[0]))
        elif mutation=="reference_exceeds_camera":
            er[0]["independent_reference_minutes"]=900
        elif mutation=="zero_reference_duration":
            er[0]["independent_reference_minutes"]=0
        _write(e,REQUIRED_EFFORT,er)
        with pytest.raises(ValueError,match=message):
            audit(e,p)


def test_zero_passage_stratum_is_defined_effort_not_declared_activity_absence():
    with TemporaryDirectory() as temp:
        root=Path(temp)
        e,p,er,pr=_generate(root)
        pr=[r for r in pr if not(r["phase"]=="B" and r["clock_bin"]=="night")]
        _write(p,REQUIRED_PASSAGES,pr)
        result=audit(e,p)
        empty=next(x for x in result["strata"] if x["phase"]=="B" and x["clock_bin"]=="night")
        assert empty["independent_reference_minutes"]==600
        assert empty["species_calibration"] == []
        assert result["limits"]["reference_video_false_negative_rate_not_identified_by_this_schema"] is True
