"""Deterministic reference passage + operational overlap crosswalk tests.

All records are synthetic; no biological data or camera footage is opened.
"""
from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.independent_reference_passage_audit import (
    REQUIRED_COVERAGE, REQUIRED_EFFORT, REQUIRED_PASSAGES, audit,
)


def _write(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle,fieldnames=sorted(header))
        writer.writeheader()
        writer.writerows(rows)


def _generate(folder):
    effort=folder/"effort.csv"
    references=folder/"reference_passages.csv"
    coverage=folder/"reference_coverage_intervals.csv"
    effort_rows,pass_rows,coverage_rows=[],[],[]
    dates={"A":"2026-06-20","B":"2026-07-20"}
    index=0
    # Six hours of known reference/camera overlap, in the actual fixed
    # 21:00-04:00 and 10:00-16:00 local clock windows, respectively.
    for phase, when in dates.items():
        for clock, hour in (("night","22"),("midday","12")):
            effort_rows.append({
                "site_id":"site_1","phase":phase,"clock_bin":clock,
                "camera_operational_minutes":360,
                "independent_reference_minutes":360,
                "reference_sampling_scheme":"continuous_reference",
            })
            if clock=="night":
                start=f"{when}T21:00:00+09:00"
                next_day = "2026-06-21" if phase=="A" else "2026-07-21"
                end=f"{next_day}T03:00:00+09:00"
            else:
                start=f"{when}T10:00:00+09:00"
                end=f"{when}T16:00:00+09:00"
            coverage_rows.append({
                "interval_id":f"coverage_{phase}_{clock}",
                "site_id":"site_1","phase":phase,"clock_bin":clock,
                "reference_source_id":"independent_video_1",
                "camera_start":start,"camera_end":end,
                "reference_start":start,"reference_end":end,
            })
            registered=5 if phase=="A" else (2 if clock=="night" else 8)
            for idx in range(10):
                index+=1
                detected=idx<registered
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
    _write(effort,REQUIRED_EFFORT,effort_rows)
    _write(references,REQUIRED_PASSAGES,pass_rows)
    _write(coverage,REQUIRED_COVERAGE,coverage_rows)
    return effort,references,coverage,effort_rows,pass_rows,coverage_rows


def _test_environment():
    return TemporaryDirectory()


def test_reference_independence_and_camera_artifact_on_360min_clock_windows():
    with _test_environment() as folder:
        e,p,c,*_= _generate(Path(folder))
        result=audit(e,p,c)
        assert result["schema_version"]==2
        assert result["status"]=="TIME_WINDOW_VERIFIED_CONDITIONAL_REFERENCE_PASSAGE_CALIBRATION"
        assert result["source"]["reference_passage_rows"]==40
        assert result["source"]["verified_reference_coverage_intervals"]==4
        assert len(result["strata"])==4
        bins={(s["phase"],s["clock_bin"]):s["species_calibration"][0]
              for s in result["strata"]}
        for phase in ("A","B"):
            assert bins[(phase,"night")]["independent_reference_passages"]==10
            assert bins[(phase,"midday")]["independent_reference_passages"]==10
            assert bins[(phase,"night")]["independent_passage_rate_per_reference_hour"]==10/6
            assert bins[(phase,"midday")]["independent_passage_rate_per_reference_hour"]==10/6
        assert bins[("A","night")]["effective_detection_given_known_passage"]==.5
        assert bins[("A","midday")]["effective_detection_given_known_passage"]==.5
        assert bins[("B","night")]["effective_detection_given_known_passage"]==.2
        assert bins[("B","midday")]["effective_detection_given_known_passage"]==.8
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
    ("outside_coverage_same_clock","outside uniquely matched"),
    ("wrong_reference_source","outside uniquely matched"),
    ("passage_wrong_timezone_offset","outside uniquely matched"),
])
def test_unsafe_passage_identity_time_or_crosswalk_is_refused(mutation,message):
    with _test_environment() as folder:
        root=Path(folder)
        e,p,c,er,pr,cr=_generate(root)
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
        elif mutation=="outside_coverage_same_clock":
            pr[0]["reference_timestamp"]="2026-06-22T22:15:00+09:00"
        elif mutation=="wrong_reference_source":
            pr[0]["reference_source_id"]="wrong_video"
        elif mutation=="passage_wrong_timezone_offset":
            pr[0]["reference_timestamp"]="2026-06-20T22:15:00+08:00"
        _write(p,REQUIRED_PASSAGES,pr)
        with pytest.raises(ValueError,match=message):
            audit(e,p,c)


@pytest.mark.parametrize("mutation,message",[
    ("trigger_selected_reference","cannot be selected by camera trigger"),
    ("duplicate_effort","duplicate effort stratum"),
    ("reference_exceeds_camera","exceeds camera"),
    ("zero_reference_duration","finite and positive"),
])
def test_invalid_effort_denominators_are_refused(mutation,message):
    with _test_environment() as folder:
        root=Path(folder)
        e,p,c,er,pr,cr=_generate(root)
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
            audit(e,p,c)


@pytest.mark.parametrize("mutation,message",[
    ("missing_interval","no independently timed reference coverage"),
    ("duplicate_interval_id","duplicate reference coverage interval"),
    ("overlapping_intervals","overlapping camera coverage"),
    ("camera_duration_disagrees","camera effort minutes disagree"),
    ("reference_duration_disagrees","independent reference minutes disagree"),
    ("night_outside_bin","outside declared clock bin"),
    ("different_timezones","constant timezone offset"),
    ("no_camera_reference_overlap","no positive overlap"),
])
def test_bad_coverage_intervals_cannot_fake_reference_exposure(mutation,message):
    with _test_environment() as folder:
        root=Path(folder)
        e,p,c,er,pr,cr=_generate(root)
        if mutation=="missing_interval":
            cr.pop(0)
        elif mutation=="duplicate_interval_id":
            duplicate=dict(cr[0])
            duplicate["camera_start"]="2026-06-22T21:00:00+09:00"
            duplicate["camera_end"]="2026-06-23T03:00:00+09:00"
            duplicate["reference_start"]=duplicate["camera_start"]
            duplicate["reference_end"]=duplicate["camera_end"]
            cr.append(duplicate)
        elif mutation=="overlapping_intervals":
            duplicate=dict(cr[0])
            duplicate["interval_id"]="new_unique_overlap"
            cr.append(duplicate)
        elif mutation=="camera_duration_disagrees":
            cr[0]["camera_end"]="2026-06-21T02:00:00+09:00"
        elif mutation=="reference_duration_disagrees":
            cr[0]["reference_end"]="2026-06-21T02:00:00+09:00"
        elif mutation=="night_outside_bin":
            cr[0]["camera_start"]="2026-06-20T20:00:00+09:00"
        elif mutation=="different_timezones":
            cr[0]["reference_start"]="2026-06-20T21:00:00+00:00"
        elif mutation=="no_camera_reference_overlap":
            cr[0]["reference_start"]="2026-06-21T03:00:00+09:00"
            cr[0]["reference_end"]="2026-06-21T04:00:00+09:00"
        _write(c,REQUIRED_COVERAGE,cr)
        with pytest.raises(ValueError,match=message):
            audit(e,p,c)


def test_zero_passage_stratum_is_verified_observed_zero_not_unknown_effort():
    with _test_environment() as folder:
        root=Path(folder)
        e,p,c,er,pr,cr=_generate(root)
        pr=[r for r in pr if not(r["phase"]=="B" and r["clock_bin"]=="night")]
        _write(p,REQUIRED_PASSAGES,pr)
        result=audit(e,p,c)
        empty=next(x for x in result["strata"] if x["phase"]=="B" and x["clock_bin"]=="night")
        assert empty["independent_reference_minutes"]==360
        assert empty["verified_coverage_intervals"]==1
        assert empty["species_calibration"]==[]
        assert result["limits"]["reference_video_false_negative_rate_not_identified_by_this_schema"] is True


def test_unverifiable_missing_coverage_file_must_not_produce_detection_result():
    with _test_environment() as folder:
        e,p,c,*_= _generate(Path(folder))
        c.unlink()
        with pytest.raises(FileNotFoundError):
            audit(e,p,c)
