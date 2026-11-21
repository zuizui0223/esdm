import json
from pathlib import Path

import pytest

from scripts.neobat_independent_plot_crosswalk import audit_plot_csv

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "docs/replication/NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json").read_text())
HEADER = "source_id,source_kind,country,plot_id,taxon,origin_dataset_id\n"


def test_frozen_roster_and_country_denominators():
    assert len(MANIFEST["plant_taxa"]) == 106
    assert len(MANIFEST["shadow_fitted_countries"]) == 10
    assert MANIFEST["external_plot_observations_opened"] is False


def test_empty_source_is_not_an_ecological_negative():
    result = audit_plot_csv(MANIFEST, HEADER)
    assert result["records_read"] == 0
    assert all(x["taxa_without_observed_plot_records"] == 106 for x in result["countries"])
    assert result["plot_absences_inferred"] is False
    assert result["M3_minus_M1_auc"] is None


def test_exact_positive_records_are_counted_without_inferred_absences():
    species = MANIFEST["plant_taxa"][0]
    rows = HEADER + (
        f"A,independent_vegetation_plot,BR,P1,{species},dataset1\n"
        f"A,independent_vegetation_plot,BR,P1,{species},dataset1\n"
        f"B,independent_vegetation_plot,BR,P2,{species},dataset2\n"
        f"G,GBIF_occurrence,BR,P3,{species},dataset3\n"
    )
    result = audit_plot_csv(MANIFEST, rows)
    br = next(x for x in result["countries"] if x["country"] == "BR")
    assert br["taxa_with_observed_plot_records"] == 1
    assert br["distinct_positive_record_plots"] == 2
    assert br["distinct_origin_sources"] == 2
    assert result["rejected"]["duplicate_plot_taxon"] == 1
    assert result["rejected"]["non_independent_or_non_plot_source"] == 1
    assert result["countries_with_two_origin_sources"] == ["BR"]


def test_two_sources_in_one_country_do_not_become_two_countries():
    species = MANIFEST["plant_taxa"][0]
    rows = HEADER + f"A,independent_vegetation_plot,BR,P1,{species},dataset1\nB,independent_vegetation_plot,BR,P2,{species},dataset2\n"
    result = audit_plot_csv(MANIFEST, rows)
    assert len(result["countries_with_two_origin_sources"]) == 1


@pytest.mark.parametrize("row", [
    "A,independent_vegetation_plot,BR,,Ficus insipida,dataset1\n",
    "A,independent_vegetation_plot,BR,P1,,dataset1\n",
    "A,independent_vegetation_plot,BR,P1,Ficus insipida,\n",
])
def test_missing_provenance_fails_closed(row):
    with pytest.raises(ValueError):
        audit_plot_csv(MANIFEST, HEADER + row)


def test_duplicate_header_fails_closed():
    with pytest.raises(ValueError):
        audit_plot_csv(MANIFEST, HEADER.strip() + ",country\n")


def test_manifest_drift_fails_closed():
    changed = dict(MANIFEST, plant_taxa=MANIFEST["plant_taxa"][:-1])
    with pytest.raises(ValueError):
        audit_plot_csv(changed, HEADER)


def test_source_aliases_do_not_create_independent_origin_datasets():
    species = MANIFEST["plant_taxa"][0]
    rows = HEADER + (
        f"A,independent_vegetation_plot,BR,P1,{species},dataset1\\n"
        f"B,independent_vegetation_plot,BR,P2,{species},dataset1\\n"
    )
    result = audit_plot_csv(MANIFEST, rows)
    br = next(x for x in result["countries"] if x["country"] == "BR")
    assert br["distinct_origin_sources"] == 1
    assert result["countries_with_two_origin_sources"] == []


def test_one_source_alias_cannot_map_to_two_primary_datasets():
    species = MANIFEST["plant_taxa"][0]
    rows = HEADER + (
        f"A,independent_vegetation_plot,BR,P1,{species},dataset1\\n"
        f"A,independent_vegetation_plot,BR,P2,{species},dataset2\\n"
    )
    with pytest.raises(ValueError, match="conflicting origin datasets"):
        audit_plot_csv(MANIFEST, rows)
