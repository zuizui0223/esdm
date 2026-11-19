# NeoBat full 106×17 plant source-transfer dual-implementation replay audit — freeze

Date: 2026-11-19. This audit does not open original GBIF records, plant coordinates, raster pixels, or new biological outcomes. It compares **only previously generated aggregate plant×country source-rank AUCs and original input-count receipts**. It is not independent ecological or external-source replication because both completed analyses read the same DOI source and share some same utility functions.

## Frozen prior evidence (no post-hoc species deletion)

- **Implementation A**: existing research branch commit `4cf7c601473f70daa9f9ff5cbf7b30c3c0abb41a`, original [Actions #44538948274](https://github.com/zuizui0223/esdm/actions/runs/44538948274); original per-fold JSON `docs/replication/neobat/plant_106x17_source_effort_transfer.json`, blob SHA-1 `3389fda966cb3c7566ff5d249396fed725f16a05`.
- **Implementation B**: independent branch commit `e940be5799bb98c59f708cb6da454f11d1f24b30`, [Actions #44540297088](https://github.com/zuizui0223/esdm/actions/runs/44540297088); per-fold JSON `docs/replication/neobat/plant_106x17_source_intensity_diagnostic.json`, blob SHA-1 `7a84042d25f4809e5169da6881242b33170be7d0`.
- Source: same DOI `10.15468/dl.xwc5zf`, same original 367,988 plant source ZIP, same WorldClim original BIO1/BIO12 and elevation, same 106 plants × 17 country fixed 1,802 cohort, same Colombia original 3 sentinel source-matched AUCs, and identical model hyperparameters. **Shared data and subroutines preclude independent ecological confirmation.**

## Predetermined comparison

Compare all **1,802** matched (original fixed plant name, heldout country) keys, without sampling, taxon changes or selecting only successful fits. Check all source-data denominators that both implementations export: train/test focal and background cells; test environmental nodata exclusions. Map A's per-fold statuses (fit vs source/quantity STOP) to B's statuses, and require **exactly the same 647 fitted pairs** and 1,155 stopped pairs.

On all fitted pairs, compare numerical AUCs for abiotic-only, original source-intensity-only, combined, and combined-minus-intensity (absolute difference <=1e-10), plus exact-intensity-matched conditional AUC and comparable pair fraction (allow both-null where no comparable pairs). Fail closed on any single different status, denominator, outcome, cohort source hash or plant/region count. Report maximum absolute numerical difference, number of exact discrepancies >1e-12, status mismatch count and original three sentinel replay flags. **Do not optimize/change either model based on the comparison.**

A passed audit is computational reproducibility of the source-recording diagnostic within a shared data ecosystem. The biological bat `M3−M1` and `M3−N1` remain null/unestimated; neither AUC test proves food resources, true absence, occupancy or causality.

No source per-cell records or predictors are materialized; only the two pinned aggregate JSON results are read. No modification to `main`.
