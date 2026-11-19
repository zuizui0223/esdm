# NeoBat 106×17 original botanical source-transfer: cross-implementation full 1,802-fold audit

Date: 2026-11-19. **Computational equivalence verified, not a new ecological finding.**

## Evidence

- Existing 106×17 plant source-transfer run [Actions #44538948274](https://github.com/zuizui0223/esdm/actions/runs/44538948274), commit `4cf7c601473f70daa9f9ff5cbf7b30c3c0abb41a`.
- A separately written implementation from the same underlying plant DOI and common source utilities ran successfully in [Actions #44540297088](https://github.com/zuizui0223/esdm/actions/runs/44540297088), pinned commit `e940be5799bb98c59f708cb6da454f11d1f24b30`.
- Prospective frozen aggregate comparison [Actions #44541456608](https://github.com/zuizui0223/esdm/actions/runs/44541456608) **PASS**, exact output `docs/replication/neobat/two_implementation_replay.json`.
- Extra source-only regression with independent **climate and elevation source SHA match** [Actions #44541756199](https://github.com/zuizui0223/esdm/actions/runs/44541756199) **PASS**.

Both models reproduce **all original 1,802 source-defined plant×country combinations**, with the same 647 computed rank AUCs and 1,155 source/raster/quantity STOPs. All 1,802 observed train/test positive and background counts, heldout raster no-data exclusions, all eligible AUCs (abiotic-only, other-plant-intensity-only, combined), added-abiotic AUC contrast and exact source-intensity conditional AUC/eligible-pair fractions agree to an absolute tolerance `1e-10`. **Observed maximum numerical difference: 0.0**; source-denominator, status and AUC mismatches: **0**. Existing three originally frozen Colombian plant sentinel models were reproduced by both.

Verified country-equal mean added abiotic AUC: **+0.0253913**. This is predictive additional information about **GBIF source-recorded plant relative ranks** given the sampled botanical target-group background, not calibrated plant occupancy or fruit biomass. Source-intensity observation counts remain a dominant predictor, not an independent survey-effort measurement. The independently named implementations **share the same original GBIF/WorldClim ZIPs, multiple common utility functions and model settings**, so the exact agreement is a strong **reproducibility audit**, not independent biological replication or evidence of a universal ecological law.

### Consequence for M1–M3

The already-opened DOI source and incomplete independent forest/survey-effort and true plant resource predictors do **not** permit promotion to actual bat M3−M1 or M3−N1 findings. The original v1 255-plant contract remains frozen and **not fitted**; the exploratory fixed-106 v2 continues as a separate program with **79/84** bat×country input candidates. The complete botanical rank diagnostic does **not** provide deployable 106×17 plant resource suitability surfaces for every bat/background cell. Do not transform high source-intensity AUC directly into fruit availability.

No original botanical coordinates, GBIF record rows, dataset IDs or raster pixels are opened by the aggregate audit; only two pinned aggregate JSON receipts are compared. Main unchanged.
