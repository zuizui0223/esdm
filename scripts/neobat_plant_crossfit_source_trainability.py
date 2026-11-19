"""Count fixed-candidate NeoBat plant crossfit trainability from existing DOI QC.

No raw occurrence rows, new network, biological model fit or heldout AUC.
A missing or inadequate training source is never silently encoded as zero
plant suitability. This is a prefit source-availability diagnostic.
"""
from __future__ import annotations
import argparse, json, pathlib
from datetime import datetime, timezone
from collections import Counter

from scripts.neobat_summarize_full_source_qc import EXPECTED

QC = "docs/replication/neobat/gbif_full_source_qc.json"
ROSTER = "docs/replication/neobat/NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json"


def derive(qc, roster):
    if qc.get("status")!="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED":
        raise ValueError("FULL_DOI_SOURCE_QC_STOP")
    plant=qc["groups"]["plant"]
    expect=EXPECTED["plant"]
    if (plant.get("DOI")!=expect["doi"] or
        plant.get("source_archive_sha256")!=expect["archive_sha"] or
        plant.get("full_archive_rows_checked")!=expect["n_records"]):
        raise ValueError("PLANT_SOURCE_DOI_SHA_COUNT_MISMATCH")
    if roster.get("status")!="PREFIT_DISCOVERY_ELIGIBILITY_FROZEN_NOT_INDEPENDENT_VALIDATION":
        raise ValueError("ROSTER_NOT_FROZEN")
    rows=plant.get("species_country_summary")
    species=plant.get("species_summary")
    if not isinstance(rows,list) or not isinstance(species,list) or len(species)!=255:
        raise ValueError("PLANT_COHORT_INCOMPLETE")
    universe={x["taxon"] for x in species}
    if len(universe)!=255:
        raise ValueError("PLANT_SPECIES_DUPLICATE")
    pairs=roster["strict_84_candidate_folds"]
    if len(pairs)!=84 or len({(x["bat"],x["holdout_country"]) for x in pairs})!=84:
        raise ValueError("FROZEN_84_FOLD_ROSTER_STOP")
    countries=sorted({x["holdout_country"] for x in pairs})
    if len(countries)!=17:
        raise ValueError("COUNTRY_DENOMINATOR_CHANGED")
    counts={(name,country):[0,0] for name in universe for country in countries}
    totals={name:[0,0] for name in universe}
    all_names=set()
    for x in rows:
        name,country=x["taxon"],x["country"]
        if name not in universe:raise ValueError("EXTRA_SOURCE_PLANT")
        all_names.add(name)
        strict=int(x["precision_le12500m_25km_cells"])
        indexed=int(x["recorded_25km_cells"])
        if strict<0 or indexed<strict:raise ValueError("BAD_CELL_COUNTS")
        totals[name][0]+=strict
        totals[name][1]+=indexed
        if country in countries:counts[name,country]=[strict,indexed]
    out=[]
    globally_viable=[]
    for country in countries:
        # A species with insufficient outcountry spatial cells cannot
        # provide its own independent country-crossfit plant SDM.
        strict_out={name:totals[name][0]-counts[name,country][0] for name in universe}
        indexed_out={name:totals[name][1]-counts[name,country][1] for name in universe}
        eligible20=sum(v>=20 for v in strict_out.values())
        out.append({
            "holdout_country":country,
            "strict_trainable_20plus_outcountry_cells":eligible20,
            "strict_5plus_outcountry_cells":sum(v>=5 for v in strict_out.values()),
            "strict_1plus_outcountry_cell":sum(v>=1 for v in strict_out.values()),
            "strict_zero_outcountry_cells":sum(v==0 for v in strict_out.values()),
            "strict_lt20_outcountry_cells":255-eligible20,
            "indexed_20plus_outcountry_cells":sum(v>=20 for v in indexed_out.values()),
            "indexed_zero_outcountry_cells":sum(v==0 for v in indexed_out.values()),
            "full_255_strict_training_supported":eligible20==255,
            "outcountry_nonobservation_is_not_true_plant_absence":True
        })
    for name in universe:
        if all(totals[name][0]-counts[name,country][0]>=20 for country in countries):
            globally_viable.append(name)
    n20={r["holdout_country"]:r["strict_trainable_20plus_outcountry_cells"] for r in out}
    return {
        "schema_version":1,
        "status":"FROZEN_DOI_PLANT_CROSSFIT_SOURCE_TRAINABILITY_ONLY",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "bat_source_and_response_opened":False,
        "plant_source_rows_opened":False,
        "based_on_existing_full_DOI_source_QC_only":True,
        "plant_GBIF_DOI":expect["doi"],
        "source_archive_sha256":expect["archive_sha"],
        "candidate_species_universe":255,
        "candidate_folds":84,
        "candidate_countries":len(countries),
        "strict_20cell_globally_trainable_in_all_17_holdouts":len(globally_viable),
        "strict_global_any_recorded_cell_species":sum(v[0]>0 for v in totals.values()),
        "strict_global_zero_recorded_cell_species":sum(v[0]==0 for v in totals.values()),
        "indexed_global_zero_recorded_cell_species":sum(v[1]==0 for v in totals.values()),
        "folds_whose_entire_255_species_pool_has_20plus_outcountry_strict_cells":
            sum(n20[x["holdout_country"]]==255 for x in pairs),
        "per_country":out,
        "M3_minus_M1_heldout_auc":None,
        "no_biological_model_fitted":True,
        "no_missing_species_imputed_as_zero":True,
        "must_preserve_fixed_255_candidate_universe_and_label_unfittable_species":True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="docs/replication/neobat/plant_crossfit_source_trainability.json")
    a=p.parse_args()
    dest=pathlib.Path(a.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=derive(json.loads(pathlib.Path(QC).read_text()),
                      json.loads(pathlib.Path(ROSTER).read_text()))
    except Exception as exc:
        result={"schema_version":1,"status":"PLANT_CROSSFIT_SOURCE_TRAINABILITY_STOP",
                "error_type":type(exc).__name__,"error_code":str(exc)[:200],
                "M3_minus_M1_heldout_auc":None}
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_PLANT_CROSSFIT_SOURCE",result["status"],flush=True)
    if "per_country" in result:
        print("PLANT_STRICT_20_ALL_COUNTRIES",result["strict_20cell_globally_trainable_in_all_17_holdouts"])
        print("PLANT_STRICT_COUNTRY_RANGES",min(x["strict_trainable_20plus_outcountry_cells"] for x in result["per_country"]),
              max(x["strict_trainable_20plus_outcountry_cells"] for x in result["per_country"]))
    return 0 if result["status"]=="FROZEN_DOI_PLANT_CROSSFIT_SOURCE_TRAINABILITY_ONLY" else 3


if __name__=="__main__":
    raise SystemExit(main())
