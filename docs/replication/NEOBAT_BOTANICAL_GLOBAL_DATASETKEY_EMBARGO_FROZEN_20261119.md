# NeoBat botanical cross-country source independence gate — pre-result freeze (2026-11-19)

**Status:** New exploratory diagnostic, not a confirmatory study. The full 106-plant × 17-country GBIF botanical-record transfer AUCs and three Colombia sentinels were already seen. Keep the original source-effort result unchanged; do not select taxa or holdouts based on this result.

## Question

When leaving a **country** out, did the botanical plant source model train on observations from the **same original GBIF datasetKey** that also contributed records in the withheld country? If so, can the predictor be trained after a **whole-dataset source embargo**? This measures **input support** for cross-source transfer, not independent biological plant suitability.

## Inputs already pinned

- The 106 fixed plant names and SHA `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`. The original **17** withheld countries and all **1,802** plant×country pairs are unchanged.
- Published GBIF **plant** download `10.15468/dl.xwc5zf`, original `367,988` records, immutable original ZIP SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`, original accepted 255 name keys and prior source full-QC strict per-species×country EPSG:6933 25km cell-count receipt.
- Prior source matching gate `plant_dataset_matched_106x17_compact.json`, prior original 1802-fold AUC source transfer `plant_106x17_source_effort_transfer_compact.json`.

## Locked leakage audit and thresholds (freeze before original source-key values are re-read)

1. In-memory only, stream the original already-DOI-authenticated ZIP; for each original source row with original query year **2000–2025** and `countryCode` from the fixed 29-country universe, retain its **nonempty original `datasetKey`** in the country-specific embargo set. Do so **regardless of precision/coordinates or plant name**, because a source contributes to the withheld country's observation process even if a particular record has missing positional uncertainty. No GBIF POST or new cohort.
2. Reproduce strict 25km known-precision cell sets and full source-QC counts exactly, using existing reader. Keep all cell/source-key mappings in RAM, never in receipts.
3. For each heldout country `h`, **exclude from training in all 28 other countries every GBIF plant datasetKey present in the heldout-country embargo set**, including keys that occur for non-focal plant species. This prevents any *identical original GBIF dataset* from appearing in both training and test. The test source remains unchanged from the earlier source-matched test and still uses within-`datasetKey` other-plant pseudo-background.
4. Compute source-matched positive and background cells per dataset and country as before: a dataset must have >=1 focal plant cell and >=1 nonfocal plant cell in that country. Background cells with any focal plant observation from any source cannot be used. Original distinct cell sets; no known focal absence implied. Retain all plant taxa/other-taxon records as already original GBIF.
5. For each candidate country, exclude all **source-observed 25km cell IDs** in the withheld country from training, even if a different country labels the coarse same cell.
6. `P_train>=20`, `B_train>=20`; `P_test>=5`, `B_test>=5` are fixed source-quantity gates (before environmental nodata), matching the previous source input gate. No data-dependent threshold relaxation or replacement plants.
7. All 1,802 pairs must be accounted as qualified or stopped, and per-country 106 fixed-plant denominator retained. Report total test-scorable/only-training-eligible, ratio vs prior **677 source-scorable pairs**, number of countries with all 106 plants trainable, the three frozen Colombia sentinel pairs and source-embargo dataset key *counts* per country. Report median source-dataset share and other aggregate descriptive shares; never IDs.
8. The previous `plant_dataset_matched_106x17` per-country *training and test counts must be reproduced exactly without any embargo*, before the new source-loss results are accepted. This guards against unintended denominator/reader drift. Strict full DOI source-QC per species×country 25km counts must match as well.
9. Separate later, **only if source quantity supports it**, a new frozen *exploratory cross-source plant AUC* design would refit 106 species on country- and dataset-embargoed data with exactly the same fixed three models and environmental rasters; this gate itself fits **no** plant or bat models.

## Scientific limits

- Distinct GBIF `datasetKey` means distinct GBIF dataset IDs, **not** independent survey crews, detection effort, identical source-provider disjointness, specimen abundance, resource biomass, true plant absence, or fruiting/feeding. The original plant occurrence source has already been opened; this is **post-hoc source robustness**, not independent external confirmation.
- If most fixed plant models cannot be trained after embargo, document a **transportability/identifiability ceiling**. Do not claim a negative ecological fruit-link result, infer zeros for missing plants, or upgrade the unestimated original M1-vs-M3 or M3-vs-N1 bat comparison.
- Do not export raw coordinates, original GBIF rows, `datasetKey`, original reference IDs, 25km cell IDs, or source-level species×cell matrices.
