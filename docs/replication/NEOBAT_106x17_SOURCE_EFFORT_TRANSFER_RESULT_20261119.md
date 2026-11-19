# NeoBat fixed 106-plant × 17-country botanical source transfer result

Date: 2026-11-19. Predefined exploratory program:
`docs/replication/NEOBAT_106x17_PLANT_SOURCE_EFFORT_TRANSFER_FROZEN_20261119.md`.

Original ZIP-backed model run [Actions #44538948274](https://github.com/zuizui0223/esdm/actions/runs/44538948274) **succeeded**, after source-free synthetic code/region-weight tests [Actions #44538765606](https://github.com/zuizui0223/esdm/actions/runs/44538765606) PASSED. The original 367,988 GBIF plant-record ZIP, WorldClim BIO1/BIO12 and elevation source byte hashes, fixed 106-plant universe, all existing strict country×species cell counts and the **three previous Colombia dataset-matched sentinel AUCs and train/test denominators** were replayed exactly. No original rows, coordinates, raster pixels, source dataset IDs, per-cell scores or sensitive positions were saved.

- Full receipt `docs/replication/neobat/plant_106x17_source_effort_transfer.json` (all original 1,802 plant×country pairs including source/raster/test-class stops).
- Small inspectable receipt `docs/replication/neobat/plant_106x17_source_effort_transfer_compact.json`.

## Empirical outcomes: prediction of botanical GBIF recorded-cell ranks ONLY

| Summary | Source-replayed exploratory outcome |
|---|---:|
| Original fixed cohort | 106 species × 17 withheld countries = **1,802** |
| Country-heldout relative rank AUC actually evaluable | **647/1,802** |
| Original candidate pairs stopped for source, class or nodata insufficiency | **1,155/1,802** |
| Species represented by ≥1 evaluated test | **105/106** |
| Countries represented | **17/17** |
| `AUC(BIO1+BIO12+ELEV+source-intensity) − AUC(source-intensity only)`, per species×country equal | **+0.02972** |
| Same contrast, per country equal | **+0.02539** |
| Same contrast, per species equal | **+0.03009** |
| 2,000-draw country-resampled descriptive percentile interval | **+0.01534 to +0.03733** |
| Leave-one-country-out country-equal mean range | **+0.02139 to +0.02759** |
| Evaluated pairs with positive extra abiotic AUC | **66.9%** |
| Evaluated pairs with extra abiotic AUC > +0.02 | **45.1%** |
| Evaluated pairs with extra abiotic AUC < −0.02 | **15.3%** |

Important spatial heterogeneity: Peru had the largest country-equal increment (+0.0894), Ecuador (+0.0527) and Guatemala (+0.0456) were positive; Argentina (−0.0098) and French Guiana (−0.0030) were negative; El Salvador (+0.0008) was essentially zero. These are country-specific source recording rank comparisons, not independently sampled ecological effects. The positive country-resampled descriptive interval does **not** establish unobserved-source replication, true occupancy generalization, causality, or a novel universal resource law. Multiple overlapping plant species and source datasets induce residual dependencies beyond the country bootstrap.

## Scope of supported interpretation

**Better broad geographic predictive portability of botanical source records is detectable with coarse abiotic covariates even after accounting for the source-derived count of other recorded plant taxa.** The average added AUC is modest (~0.025), and the *reporting-intensity covariate* was the dominant predictive feature in the earlier fixed Colombia sentinel models. Since that covariate mixes real plant richness with collection/reporting effort and the GBIF pseudo-background contains unknown focal occupancy, AUC is discrimination of source-observed records, not calibrated ecological plant occurrence or actual fruit availability. The original 3 Colombia sentinels showing little added abiotic rank were atypical within this **observed source cohort**, not a universal environmental null.

Consequently, this research **does not** yet test whether true documented bat fruit partners predict bat source-independent geography above M1 and source-rewired N1. Real bat ecological M3−M1 and M3−N1 are **null/unestimated**. To move from methodology to biology, need source-independent or explicitly calibrated plant distribution/resource predictors, full-country forest and detection-effort covariates, and bat target-group background with source-independent outer holdouts. The 255-plant v1 protocol remains frozen; 106-plant v2 is a separate exploratory model universe. No changes to `main`.

## Next operational decision

Keep the strict original 84-fold bat denominator and the previously qualified **79** bat×country candidates as an accounting opportunity only, not 79 completed ecology models. Do **not** silently use high GBIF source-effort AUC as biological food abundance and do not promote a positive trophic SDM claim based on this audit. The next task is an explicit environment/predictor independent-source or detection-proxy calibration and then an exactly paired exploratory bat M0/M1/M3/N1 comparison against the degree-preserving N1 null; any truly confirmatory conclusion will need a distinct untouched observation source/period.
