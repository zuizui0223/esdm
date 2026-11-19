# NeoBat plant 106×17 within-GBIF-datasetKey source matching feasibility — frozen preflight

Date: 2026-11-19. Strictly **exploratory source observability**, following the already-opened 3-plant Colombia outcomes and the post-hoc source-intensity diagnostic. Not an independent test, a source-specific plant SDM, bat M1/M3/N1 result, or ecological proof.

## Fixed input

- Use the original 367,988-record GBIF plant DOI `10.15468/dl.xwc5zf`, exact ZIP SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`, original accepted 255 names, 2000–2025 known coordinateUncertainty <=12,500 m, EPSG:6933 25km cells. Re-download **without issuing a new GBIF download request**, and replay every previous species×country unique-cell count; STOP on drift.
- Fixed 106-plant intersection from `v2_106plant_reference_input_gate.json`, sorted SHA-256 `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`. Fixed 17 withheld countries from the original 84 bat×country source roster. No taxon, country or threshold may be changed after inspecting results.

## Source-controlled pseudo-background construction

For each focal plant `p` and country `c`, inspect only **distinct nonempty original GBIF datasetKey values that contain the focal plant** in that country. A dataset is *eligible* only if it contains at least one strict-grid cell of `p` and **at least one** recorded cell of any other plant taxon in the same country. The source-qualified focal positive set is the union of `p` cells from these eligible datasets. The background set is the union of cells having other plant taxa recorded in those exact eligible datasets, **excluding any cell with `p` recorded by any data source**. Count unique cells, not individual records. This is matching to a *source collection*, not proof of a shared survey time/event or independently enumerated detection effort.

For an outer holdout `h`: test positives/background are only from `h`. Training positives/background combine 28 other original countries and exclude every 25km grid cell that also has **any plant GBIF record in h**, even if the training record was assigned to a different country at a border. This spatial-cell embargo is frozen, as in the previous three-species pilot.

## Frozen quantities

For **all 106 plant species × all 17 heldout countries = 1,802 pairs**, report aggregate `test_focal_cells`, `test_source_matched_otherplant_background_cells`, `train_focal_cells`, `train_source_matched_otherplant_background_cells`, and numbers of eligible source datasets `n_datasetKey` in test and training (NOT their IDs). Define full source quantity qualified if **test >=5 of each class and training >=20 of each class**; additionally count source-only trainable status if `train_P>=20 & train_B>=20` regardless of test support. Do not silently interpret any missing focal record as species absence. Summarize per heldout country trainable plant count **out of 106**, complete-106 availability, test-scoring eligibility, and the fixed Colombia 3 sentinel results with no outcome-based replacement. Cross-country 106-plant prediction could be trained from this strict subset ONLY if each of the 106 species has adequate training class support in every original fold, not by silently setting untrained plant relative suitability to zero.

No source dataset IDs, plant occurrence coordinates, cell IDs, raw source rows, per-cell effort counts, or raster pixels may be stored. This stage fits **zero plant or bat models** and never computes heldout AUC. All 1,802 source stops remain in the denominator. No changes to v1 primary M0/M1/M3/N1 ecology or main.
