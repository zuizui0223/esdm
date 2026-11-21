"""Behavioral checks for survey-frame ranking and public-only output."""
import json
import math

import pytest

from scripts.neobat_bien_external_plant_diagnostic import (
    evaluate_country, pairwise_auc, prepare_records,
)


def row(taxon, cell, frame="A", year="2005-01-02", precision=100, **extra):
    return {
        "scrubbed_species_binomial": taxon,
        "longitude": cell, "latitude": 1,
        "datasource_id": 18, "datasource": "provider", "dataset": "dataset",
        "sampling_protocol": frame, "plot_area_ha": 1,
        "date_collected": year, "coord_uncertainty_m": precision,
        **extra,
    }


def run(rows, scores, taxa=("Focal",), train=None):
    records = prepare_records(rows, lambda lon, lat: (math.floor(lon), math.floor(lat)))
    predictions = {(cell, 1): {taxon: score for taxon in taxa}
                   for cell, score in scores.items()}
    return evaluate_country("CR", taxa, records, predictions,
                            train or {taxon: set() for taxon in taxa})


def mode(result, taxon="Focal", name="primary_2000_2025"):
    return next(r for r in result["taxon_results"] if r["taxon"] == taxon)["modes"][name]


def estimable_frames(result, **kwargs):
    return [r for r in mode(result, **kwargs)["frame_results"] if r["auc"] is not None]


def test_duplicate_records_and_subplots_do_not_increase_cell_weights():
    rows = [row("Focal", 1), row("Other", 2), row("Other", 3)]
    original = run(rows, {1: .7, 2: .6, 3: .8})
    duplicated = run(rows * 8 + [row("Focal", 1, subplot="other", individual_count=500)],
                     {1: .7, 2: .6, 3: .8})
    for result in (original, duplicated):
        contrast = estimable_frames(result)[0]
        assert (contrast["positive_cells"], contrast["background_cells"], contrast["auc"]) == (1, 2, .5)


def test_known_positive_in_another_frame_or_date_never_becomes_background():
    rows = [row("Focal", 1, "A", year="1990"),
            row("Other", 1, "B"), row("Focal", 2, "B"), row("Other", 3, "B")]
    contrast = estimable_frames(run(rows, {1: .99, 2: .8, 3: .2}))[0]
    assert contrast["background_cells"] == 1
    assert contrast["known_positive_background_exclusions"] == 2
    assert contrast["auc"] == 1


def test_comparisons_are_within_frames_and_not_a_pooled_auc():
    rows = [row("Focal", 1, "A"), row("Other", 2, "A"),
            row("Focal", 3, "B"), row("Other", 4, "B")]
    result = run(rows, {1: .4, 2: .3, 3: .9, 4: .8})
    assert [r["auc"] for r in estimable_frames(result)] == [1, 1]
    assert mode(result)["method_metadata_present"]["mean_frame_auc"] == 1
    assert pairwise_auc([.4, .9], [.3, .8]) == .75


def test_actual_training_cell_union_is_removed_from_both_test_classes():
    rows = [row("Focal", 1), row("Focal", 2), row("Other", 3), row("Other", 4)]
    result = run(rows, {1: .9, 2: .8, 3: .2, 4: .1},
                 train={"Focal": {(1, 1), (4, 1)}})
    contrast = estimable_frames(result)[0]
    assert contrast["positive_training_overlap_excluded"] == 1
    assert contrast["background_training_overlap_excluded"] == 1
    assert contrast["positive_cells"] == contrast["background_cells"] == 1
    assert contrast["auc"] == 1


def test_training_overlap_is_taxon_specific():
    rows = [row("Focal", 1), row("Second", 2), row("Other", 3)]
    result = run(rows, {1: .9, 2: .8, 3: .1}, taxa=("Focal", "Second"),
                 train={"Focal": {(1, 1)}, "Second": set()})
    assert mode(result)["status"] == "NO_ELIGIBLE_POSITIVE_CELLS"
    assert mode(result, taxon="Second")["status"] == "EVALUABLE_EXPLORATORY"


def test_missing_taxon_remains_unknown_in_every_mode():
    result = run([row("Focal", 1), row("Other", 2)], {1: .9, 2: .1},
                 taxa=("Focal", "Unobserved"))
    missing = next(r for r in result["taxon_results"] if r["taxon"] == "Unobserved")
    assert len(result["taxon_results"]) == 2
    assert missing["matched_records"] == 0
    for value in missing["modes"].values():
        assert value["status"] == "NO_MATCH_UNKNOWN"
        assert value["method_metadata_present"]["mean_frame_auc"] is None


def test_dates_and_missing_precision_are_separate_fixed_modes():
    rows = [row("Focal", 1, year="1995"), row("Focal", 2, year=None),
            row("Focal", 3, year="2020-02-01", precision=999),
            row("Focal", 4, year="2020", precision=None),
            row("Focal", 5, year="2026"), row("Focal", 6, precision=20000),
            row("Focal", 7, precision=-1), row("Other", 8)]
    result = run(rows, {i: i / 10 for i in range(1, 9)})
    assert mode(result)["retained_positive_cells"] == 2
    assert mode(result, name="known_precision_2000_2025")["retained_positive_cells"] == 1
    assert mode(result, name="historical_undated_descriptive")["retained_positive_cells"] == 4
    assert mode(result)["eligible_positive_records_unknown_precision"] == 1
    assert result["coverage"]["records_after_2025"] == 1
    assert result["coverage"]["records_invalid_precision"] == 1


def test_missing_method_metadata_is_not_summarized_as_documented():
    result = run([row("Focal", 1, frame=None), row("Other", 2, frame=None)], {1: .8, 2: .2})
    assert result["frames"][0]["method_class"] == "METHOD_METADATA_MISSING"
    assert mode(result)["method_metadata_present"]["mean_frame_auc"] is None
    assert mode(result)["method_metadata_missing"]["mean_frame_auc"] == 1


def test_area_or_growth_form_change_creates_a_separate_frame():
    rows = [row("Focal", 1, plot_area_ha=.1), row("Other", 2, plot_area_ha=1),
            row("Other", 3, plot_area_ha=.1, growth_forms_included_lianas=True)]
    result = run(rows, {1: .8, 2: .2, 3: .1})
    assert len(result["frames"]) == 3
    assert mode(result)["status"] == "NO_WITHIN_FRAME_COMPARISON"


def test_invalid_environment_is_counted_and_not_an_absence():
    result = run([row("Focal", 1), row("Focal", 2), row("Other", 3)], {2: .8, 3: .2})
    contrast = estimable_frames(result)[0]
    assert contrast["positive_raster_invalid_excluded"] == 1
    assert contrast["positive_cells"] == 1


def test_ties_count_half_and_nonfinite_scores_fail_loudly():
    assert pairwise_auc([.5], [.5]) == .5
    assert pairwise_auc([], [.5]) is None
    with pytest.raises(ValueError, match="finite"):
        pairwise_auc([float("nan")], [.5])


def test_public_output_has_no_raw_locations_plot_names_or_predictions():
    rows = [row("Focal", 12.3456789, latitude=23.456789,
                plot_name="SECRET_SITE_MARKER", subplot="SECRET_SUBPLOT_MARKER"),
            row("Other", 13.3456789, latitude=23.456789)]
    records = prepare_records(rows, lambda lon, lat: (math.floor(lon), math.floor(lat)))
    result = evaluate_country("CR", ("Focal",), records,
                              {(12, 23): {"Focal": .9123456}, (13, 23): {"Focal": .1234567}},
                              {"Focal": set()})
    serialized = json.dumps(result)
    for marker in ("SECRET_", "12.3456789", "23.456789", "0.9123456", "0.1234567"):
        assert marker not in serialized
    def check_keys(value):
        if isinstance(value, dict):
            assert not {"latitude", "longitude", "plot_name", "subplot", "cells", "scores"}.intersection(value)
            for item in value.values():
                check_keys(item)
        elif isinstance(value, list):
            for item in value:
                check_keys(item)
    check_keys(result)


def test_missing_prediction_taxon_is_an_integrity_error():
    records = prepare_records([row("Focal", 1), row("Other", 2)], lambda x, y: (int(x), int(y)))
    with pytest.raises(ValueError, match="taxon"):
        evaluate_country("CR", ("Focal",), records,
                         {(1, 1): {}, (2, 1): {"Focal": .1}}, {"Focal": set()})


def test_invalid_geographic_coordinates_are_excluded_before_projection():
    records = prepare_records([row("Focal", 1, latitude=100),
                               row("Focal", 1, precision=0), row("Other", 2)],
                              lambda x, y: (int(x), int(y)))
    result = evaluate_country("CR", ("Focal",), records,
                              {(1, 1): {"Focal": .8}, (2, 1): {"Focal": .2}}, {"Focal": set()})
    assert result["coverage"]["records_invalid_coordinates"] == 1
    assert mode(result, name="known_precision_2000_2025")["retained_positive_cells"] == 1


def test_missing_source_metadata_and_name_stay_explicit_in_full_frame():
    rows = [row("Focal", 1, datasource_id=None),
            row(None, 2, datasource_id=None)]
    result = run(rows, {1: .8, 2: .2})
    assert result["frames"][0]["datasource_id"] == ""
    assert result["coverage"]["records_missing_datasource_id"] == 2
    assert result["coverage"]["records_missing_species_name"] == 1
    contrast = estimable_frames(result)[0]
    assert contrast["positive_cells"] == contrast["background_cells"] == 1
