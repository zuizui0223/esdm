# NeoBat fixed 106-plant full-model trainability *after raster no-data* — prefit gate

Date: 2026-11-19. New analysis of **already generated aggregate original DOI receipts**, no original biological rows or source rasters accessed in this stage. This gate does not fit M1, M3, N1 or plant models and does not reopen a heldout species response. The 255-plant v1 is frozen and unestimated; 106-plant v2 is exploratory.

## Frozen inputs

- **Plant country source-rank full original result:** `docs/replication/neobat/plant_106x17_source_effort_transfer.json` from committed research model run `4cf7c601473f70daa9f9ff5cbf7b30c3c0abb41a`, original JSON Git blob SHA `3389fda966cb3c7566ff5d249396fed725f16a05`. Contains all 106 plant taxa ×17 countries=1,802 with **outside-country** focal/background 25km cell counts *after* forest-independent WorldClim centroid no-data exclusions.
- **Previous source-only qualification:** `docs/replication/neobat/plant_dataset_matched_106x17_compact.json`, 1,802/1,802 plant training quantity prior to raster screening; frozen 106 name universe SHA `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`.
- **Original bat-fold denominator:** `docs/replication/neobat/bat_targetgroup_background_gate.json` (84 original source bat×country pairs, 80 bat target-background source-qualified); `docs/replication/neobat/v2_106plant_reference_input_gate.json` (83 frozen-106 original literature partner source-qualified). Their intersection was previously 79/84, **not** 79 completed ecological fits.

## Predetermined test

For every one of the 1,802 original plant×country rows count trainable plant if **both** `train_source_matched_focal_cells>=20` and `train_source_matched_target_background_cells>=20` **after original WorldClim BIO1/BIO12/ELEV no-data exclusions and source matching**. Do NOT require plant test-country positives for plant **prediction**; plant source heldout AUC cannot always be scored, but a plant suitability model could still be fitted from outside-country training if sufficient.

- Report each original 17-country `n_trainable_out_of_106`, the `n_untrainable`, and count of countries with complete 106 predictor training; report exact original fixed taxon failures as public scientific names (no source cell IDs or locations).
- Match the same original 84 bat×country folds and compute the intersection: source eligible `v2 partner >=3+refs>=2`, bat targetgroup background quantity eligible and **all 106 plant training-ready in that withheld country**. Do not drop any country or species based on source AUC or missingness.
- Report the original 79 source-qualified bat folds (as a descriptive denominator) and exact number remaining after complete 106-plant training preflight. Under the frozen full-106 universe, **do not silently reduce the plant list for a country, impute zero suitability, or select the subset with the best source AUC**.
- No source-rank AUC recalculated, no new independent ecological study, no claim of bat fruit-resource mechanism. This is an input qualification result only.

A fail closed if the original model archive source hash, fixed 1802 plant country keys, 17 countries, 106 names, or frozen 84 bat-fold denominators do not exactly match. Source effort is only a GBIF recording proxy, not independently measured sampling effort. WorldClim is 1970–2000 climate versus GBIF 2000–2025 observations.
