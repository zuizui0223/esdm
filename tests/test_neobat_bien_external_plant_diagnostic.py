"""Behavioral checks for survey-frame ranking and public-only output."""
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

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


@pytest.mark.parametrize("country", ["BR", "EC", "GF", "GT", "HN", "NI", "PE", "SV"])
def test_prelisted_new_country_uses_the_same_ranking(country):
    records = prepare_records([row("Focal", 1), row("Other", 2)],
                              lambda x, y: (int(x), int(y)))
    result = evaluate_country(country, ("Focal",), records,
                              {(1, 1): {"Focal": .8}, (2, 1): {"Focal": .2}},
                              {"Focal": set()})
    assert result["country"] == country
    for value in result["taxon_results"][0]["modes"].values():
        assert value["status"] == "EVALUABLE_EXPLORATORY"
        assert value["method_metadata_present"]["mean_frame_auc"] == 1


def test_country_outside_prelisted_ten_is_not_evaluated():
    with pytest.raises(ValueError):
        evaluate_country("MX", ("Focal",), (), {}, {"Focal": set()})


@pytest.fixture
def run_cli(tmp_path, monkeypatch):
    """Exercise CLI accounting without original archives, rasters or BIEN calls."""
    from scripts import neobat_bien_external_plant_diagnostic as diagnostic
    from scripts import neobat_bien_frozen_plant_adapter as adapter
    root = Path(diagnostic.__file__).resolve().parents[1]
    manifest = json.loads((root / "docs/replication/NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json").read_text())
    taxa = tuple(manifest["plant_taxa"])
    instances = []

    class Component:
        def __init__(self, frozen_root, archive_path, raster_dir, countries=("CR", "PA")):
            self.taxa = taxa
            self.countries = tuple(countries)
            instances.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def predict(self, country, cells):
            assert country in self.countries
            return {cell: {taxon: .8 if cell[0] == 1 else .2 for taxon in taxa}
                    for cell in cells}, frozenset()

        def training_cells(self, country, taxon):
            assert country in self.countries
            return frozenset()

        def provenance(self):
            return {"countries": list(self.countries), "pinned_package_versions_match": True,
                    "expected_fit_count": 106 * len(self.countries),
                    "completed_fit_count": 106 * len(self.countries)}

    class Transformer:
        @staticmethod
        def from_crs(*args, **kwargs):
            return SimpleNamespace(transform=lambda lon, lat: (lon * 25000, lat * 25000))

    monkeypatch.setattr(adapter, "FixedPlantComponent", Component)
    monkeypatch.setitem(sys.modules, "pyproj", SimpleNamespace(Transformer=Transformer))

    def invoke(countries=None, rows=None, receipt_countries=None, extra_args=()):
        scope = ("CR", "PA") if countries is None else tuple(countries)
        if rows is None:
            rows = {country: [row(taxa[0], 1), row("Other plant", 2)] for country in scope}
        receipt_scope = scope if receipt_countries is None else tuple(receipt_countries)
        receipt = {"status": "BIEN_EXTERNAL_ACQUISITION_COMPLETE",
                   "fixed106_taxa_sha256": diagnostic.FIXED106_SHA256,
                   "countries": {
                       country: {"total_rows": len(rows.get(country, [])),
                                 "matched_taxa": len({r["scrubbed_species_binomial"]
                                                      for r in rows.get(country, [])}.intersection(taxa))}
                       for country in receipt_scope}}
        private_path, receipt_path, output_path = (tmp_path / name for name in
                                                   ("private.json", "receipt.json", "output.json"))
        private_path.write_text(json.dumps({"countries": rows}))
        receipt_path.write_text(json.dumps(receipt))
        argv = [diagnostic.__file__, "--private-records", str(private_path),
                "--acquisition-receipt", str(receipt_path), "--frozen-root", str(tmp_path),
                "--plant-archive", str(tmp_path / "unused.zip"), "--raster-dir", str(tmp_path),
                "--output", str(output_path), *extra_args]
        if countries is not None:
            argv.extend(["--countries", ",".join(countries)])
        monkeypatch.setattr(sys, "argv", argv)
        diagnostic.main()
        return json.loads(output_path.read_text()), output_path.read_bytes()

    return invoke, instances, taxa


def test_cli_default_preserves_cr_pa_status_denominator_and_protocol(run_cli):
    invoke, instances, taxa = run_cli
    result, _ = invoke()
    assert instances[0].countries == ("CR", "PA")
    assert set(result["countries"]) == {"CR", "PA"}
    assert result["status"] == "EXPLORATORY_BIEN_CR_PA_FIXED106_PLANT_DIAGNOSTIC_COMPLETE"
    assert result["taxon_country_results_per_mode"] == 212
    assert result["comparison_frozen_commit"] == "32aa43987b5ac4e2ce4c279504ddcc9732bd0b0c"
    assert result["comparison_specification"].endswith("NEOBAT_BIEN_EXTERNAL_PLANT_DIAGNOSTIC_FROZEN_20261121.md")
    assert all(len(country["taxon_results"]) == len(taxa) == 106
               for country in result["countries"].values())


@pytest.mark.parametrize("countries", [
    ("BR", "GF", "PE"),
    ("BR", "EC", "GF", "GT", "HN", "NI", "PE", "SV"),
    ("BR", "CR", "EC", "GF", "GT", "HN", "NI", "PA", "PE", "SV"),
])
def test_cli_accounts_for_every_taxon_in_every_requested_country(run_cli, countries):
    invoke, instances, taxa = run_cli
    result, _ = invoke(countries)
    assert instances[0].countries == countries
    assert set(result["countries"]) == set(countries)
    assert result["status"] == "EXPLORATORY_BIEN_FIXED106_PLANT_DIAGNOSTIC_COMPLETE"
    assert result["taxon_country_results_per_mode"] == 106 * len(countries)
    for country in result["countries"].values():
        assert tuple(r["taxon"] for r in country["taxon_results"]) == taxa
        for value in country["coverage"]["modes"].values():
            assert value["taxon_status_counts"] == {"EVALUABLE_EXPLORATORY": 1, "NO_MATCH_UNKNOWN": 105}


def test_successfully_empty_country_keeps_all_106_unknown_in_each_mode(run_cli):
    invoke, _, taxa = run_cli
    result, _ = invoke(("BR",), rows={"BR": []})
    country = result["countries"]["BR"]
    assert result["taxon_country_results_per_mode"] == 106
    assert country["coverage"]["total_records"] == 0
    assert country["frames"] == []
    assert tuple(r["taxon"] for r in country["taxon_results"]) == taxa
    for taxon in country["taxon_results"]:
        for value in taxon["modes"].values():
            assert value["status"] == "NO_MATCH_UNKNOWN"
            assert value["method_metadata_present"]["mean_frame_auc"] is None
            assert value["method_metadata_missing"]["mean_frame_auc"] is None
    for value in country["coverage"]["modes"].values():
        assert value["taxon_status_counts"] == {"NO_MATCH_UNKNOWN": 106}


@pytest.mark.parametrize("receipt_countries", [("CR",), ("CR", "PA", "BR")])
def test_cli_rejects_acquisition_country_set_drift_before_fitting(run_cli, receipt_countries):
    invoke, instances, _ = run_cli
    with pytest.raises(RuntimeError, match="BIEN_ACQUISITION_RECEIPT_INVALID"):
        invoke(receipt_countries=receipt_countries)
    assert not instances


def test_cli_rejects_unlisted_country_before_fitting(run_cli):
    invoke, instances, _ = run_cli
    with pytest.raises((ValueError, SystemExit)):
        invoke(("MX",))
    assert not instances


def test_cli_records_selected_protocol_and_compact_output(run_cli, tmp_path):
    invoke, _, _ = run_cli
    specification = tmp_path / "precommitted.md"
    specification.write_text("Frozen comparison specification\n")
    commit = "32d949b8b63c2adfa4918fda22e842a05cd58e72"
    result, written = invoke(("BR",), extra_args=(
        "--comparison-specification", str(specification), "--comparison-commit", commit,
        "--compact-json",
    ))
    assert result["comparison_frozen_commit"] == commit
    assert result["comparison_specification"] == str(specification)
    import hashlib
    assert result["comparison_specification_sha256"] == hashlib.sha256(specification.read_bytes()).hexdigest()
    assert b"\n  " not in written
