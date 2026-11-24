# NeoBat fixed 106×17 original botanical datasetKey source-match result

Date: 2026-11-19. Frozen rules:
`NEOBAT_PLANT_WITHIN_DATASETKEY_SOURCE_GATE_FROZEN_20261119.md`.
Source-free tests PASS [Actions #44536067261](https://github.com/zuizui0223/esdm/actions/runs/44536067261). Original 367,988-row GBIF plant DOI ZIP stream, original ZIP SHA, all strict species×country 25km cells replay, and 1802-row source-only denominator PASS [Actions #44536193396](https://github.com/zuizui0223/esdm/actions/runs/44536193396).

Original DOI `10.15468/dl.xwc5zf`, exact ZIP SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`. No new GBIF download request; no coordinates/cell IDs/dataset IDs/point records exported. Full output `neobat/plant_dataset_matched_106x17.json`; inspectable summary `neobat/plant_dataset_matched_106x17_compact.json`.

## Strict source-input result

- From the frozen original **106 plant species × 17 country holdouts = 1,802**, **1,802/1,802** retain >=20 outcountry focal recorded 25km cells AND >=20 outcountry other-plant target-background cells in the fixed same-original-`datasetKey` source construction. All 17 countries retain the full 106-plant training-source *quantity*.
- **677/1,802** additionally retain >=5 focal recorded cells and >=5 source-matched background cells **inside the withheld country**, permitting an *exploratory plant heldout country source rank test*. Country-level numbers range **14–90** of 106 (CO 90, MX 73, BR 65, NI 14); all 1802 outcomes retained, including insufficient test-source cases.
- All three frozen Colombia sentinels source-qualified: *Cecropia obtusifolia* 24 test focal cells / 531 other-plant background cells (8 eligible source data sets); *Ficus insipida* 79 / 511 (26); *Piper aduncum* 63 / 527 (28). These source counts precede separate co-recording overlap and WorldClim nodata exclusions and are **not** fitted AUC.
- This source-matching approach narrows observational background to source collection groups, but a shared original GBIF dataset key does **not** prove identical survey effort, same event, detection-independent observations, true absence, mapped plant density, fruit supply or independent external replication.

## Next specific model gate

Re-run the three **same** Colombia sentinels with source-key-matched backgrounds and **identical** existing source-effort/abiotic model settings, preserve the old pilot for direct descriptive comparison. Report whether climate/elevation adds to other-plant source intensity in the source-matched model and source-matched test denominators. Do not fit all 106×17 as ecological M3 plant food maps until this known measurement confounding is resolved; forest sampling, predictor calibration and plant–bat source independence still missing.

No M1/M3/N1 ecological comparison has been performed. Original v1 255-plant model frozen and not estimated. Main untouched.
