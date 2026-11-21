# NeoBat v3 source-disjoint 35-plant partner-retention feasibility — pre-result freeze (2026-11-19)

**Scope:** A new **exploratory input feasibility** analysis, never a revised/confirmed M1–M3 ecological test. The original v1 255-plant model, exploratory v2 106-plant design, all 84 original bat×country source candidates, and the existing 51/84 raster-quantity status stay unchanged.

## Question

When all GBIF botanical datasets also present in the withheld country are excluded from **every training country**, the original fixed 106 plants are not jointly trainable for any of 17 holdouts; only 35 original plants have >=20 unique focal 25km training cells plus >=20 within-datasetKey background cells for **all** 17. Do those **same 35 plants**, chosen only by original botanical *source quantity*, still preserve >=3 author-documented fruit partners and >=2 independent source references for focal bats after the **complete NeoBat study-site reference embargo**?

## Inputs frozen before new output

1. Fixed original 106 plants and SHA `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6` from `docs/replication/neobat/v2_106plant_reference_input_gate.json`.
2. Existing source-only all-1,802 country × plant aggregate `docs/replication/neobat/plant_106x17_global_source_embargo.json` from authenticated original plant GBIF DOI `10.15468/dl.xwc5zf`; exact `SOURCE_DISJOINT` source criterion: >=20 focal and >=20 other-plant source-background 25km cells after whole-dataset country embargo. Derive a **single sorted global intersection of 35 plants** meeting both thresholds for all 17 countries. Report their sorted-name SHA256. Do **not** pick plants based on previously observed plant AUC, co-location, species ecology or bat outcome.
3. The original NeoBat authored RECORDS and SITES, Git commit `d25292d19be32a85a21c60384a3f2d818e8081de`; source text/blob SHA must match the original preflight pinned in `scripts/neobat_gbif_metadata_preflight.py`. Use *only* source `Interaction=Frugivory` and `TrophicGuild=Frugivore` links.
4. Fixed complete original 200-site, 169-reference source embargo: `docs/replication/neobat/NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json`. A reference touching a heldout country is excluded from all training country links for that fold.
5. Exact original **84** bat×country folds from `NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json`, and source-cohort 26 bats, 255 plants plus strict heldout country cell counts from original full GBIF source-QC. The independent existing bat background quantity gate `bat_targetgroup_background_gate.json` (79/84 combined with 106 partner inputs) and full-106 raster (51/84) are provenance controls only, not selectable outcomes.

## Single execution and mandatory stops

- The 35 plants are a **fixed globally intersectional source-support subset**; if it is not exactly 35, the original 106 names/SHA differs, or any of 1,802 source-input rows differs, STOP. Sorted unique name list hashed as `sha256(UTF8("\\n".join(names)+"\\n"))`.
- For all 84 original bat×country folds (no retrospective removals), calculate distinct **training** fruit-partner plant names within the fixed 35, supported by >=5 original known-precision 25km plant record cells in the withheld country, with complete original-site publication reference embargo. Count distinct author refs. **Source-only qualified** iff >=3 partner plants and >=2 original training refs. No model or diet absence inferred.
- Calculate a **focal** degree-preserving bipartite two-edge swap possibility on the full literature training-link graph restricted to the fixed 35 plants, after the same country/source embargo. A swap involving only other bat species does not qualify for a focal N1 test; its existence does not establish well-mixed N1 Monte Carlo power.
- For all 84 original folds also retain whether their prior 106-plant bat targetgroup background and previous full-106 raster source gates were satisfied, but never interpret the older 106-species raster gate as a source-disjoint 35-plant predictor raster gate. Count intersections only as diagnostic ceilings, not as eligible actual M3 evaluations.
- Output names of the 35 plants (published species names, not sensitive GBIF records), source-eligibility flags, partner/ref numbers, the original 84 bat-country fold labels, and aggregate counts only. No raw original GBIF rows, datasetKeys, 25km grid cell IDs, coordinates, per-cell predictors, original study source citation IDs or source event IDs.
- Zero new GBIF authenticated downloads, plant SDM fits or bat M0/M1/M2/M3/N1 AUCs in this stage. Original 106 and 255 source-based botanical response limitations and `main` remain unchanged.

## Interpretation and continuation

A nonzero surviving fixed35 fold set would justify **a distinct, explicitly exploratory v3 plant prediction input** with exact source-disjoint training and the *same* 35 plants in every 17-country fold. It would still need raster/source-loss audit, independent forest and survey effort, country-heldout plant predictions, bat target background, and the exact paired M3−M1/N1 score comparison before any biological inference. If <3 links remain in most folds, document this identifiability limit rather than lowering the gates or retrospectively selecting different plant names.
