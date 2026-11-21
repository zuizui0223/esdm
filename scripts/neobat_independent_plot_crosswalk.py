"""Audit *independently collected vegetation plot* input against a frozen taxon roster.

Input is a curated, provenance-qualified CSV. This is not a BIEN/GBIF downloader.
Presence is an observed plot record; missing species never implies true absence.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import defaultdict
from pathlib import Path

REQUIRED = ("source_id", "source_kind", "country", "plot_id", "taxon", "origin_dataset_id")


def audit_plot_csv(manifest: dict, text: str) -> dict:
    taxa = manifest["plant_taxa"]
    countries = manifest["shadow_fitted_countries"]
    if len(taxa) != 106 or len(set(taxa)) != 106 or len(countries) != 10 or len(set(countries)) != 10:
        raise ValueError("frozen taxon or country denominator changed")
    if manifest.get("external_plot_observations_opened") is not False:
        raise ValueError("input manifest status drifted")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or any(k not in reader.fieldnames for k in REQUIRED):
        raise ValueError("missing provenance or plot column")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("duplicate header")
    seen = set()
    source_to_dataset = {}
    matched = defaultdict(lambda: defaultdict(lambda: {"plots": set(), "sources": set()}))
    rows = 0
    in_scope = 0
    rejected = defaultdict(int)
    for row in reader:
        rows += 1
        if any(not row.get(k, "").strip() for k in REQUIRED):
            raise ValueError("blank required source/plot/taxon field")
        if row["source_kind"] != "independent_vegetation_plot":
            rejected["non_independent_or_non_plot_source"] += 1
            continue
        if row["country"] not in countries or row["taxon"] not in taxa:
            rejected["outside_frozen_country_or_taxon"] += 1
            continue
        previous = source_to_dataset.setdefault(row["source_id"], row["origin_dataset_id"])
        if previous != row["origin_dataset_id"]:
            raise ValueError("source_id maps to conflicting origin datasets")
        key = (row["origin_dataset_id"], row["plot_id"], row["taxon"])
        if key in seen:
            rejected["duplicate_plot_taxon"] += 1
            continue
        seen.add(key)
        in_scope += 1
        entry = matched[row["country"]][row["taxon"]]
        entry["plots"].add((row["origin_dataset_id"], row["plot_id"]))
        entry["sources"].add(row["origin_dataset_id"])
    summary = []
    for country in countries:
        species = matched[country]
        sources = set().union(*(v["sources"] for v in species.values())) if species else set()
        plots = set().union(*(v["plots"] for v in species.values())) if species else set()
        summary.append({
            "country": country, "fixed_taxa_denominator": 106,
            "taxa_with_observed_plot_records": len(species),
            "taxa_without_observed_plot_records": 106 - len(species),
            "distinct_positive_record_plots": len(plots),
            "distinct_origin_sources": len(sources),
        })
    eligible_countries = [v["country"] for v in summary if v["distinct_origin_sources"] >= 2]
    return {
        "schema_version": 1,
        "status": "INDEPENDENT_PLOT_POSITIVE_RECORD_AUDIT_ONLY",
        "records_read": rows, "records_in_fixed_scope": in_scope,
        "rejected": dict(sorted(rejected.items())),
        "countries": summary, "fixed_countries_denominator": 10,
        "fixed_plant_taxa_denominator": 106,
        "countries_with_two_origin_sources": eligible_countries,
        "source_independence_not_proven_by_distinct_ids": True,
        "plot_absences_inferred": False, "fruit_biomass_estimated": False,
        "bat_prediction_fitted": False, "M3_minus_M1_auc": None,
        "independent_field_source_qualification_verified_by_script": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("docs/replication/NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json"))
    parser.add_argument("--curated-plot-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = audit_plot_csv(manifest, args.curated_plot_csv.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
