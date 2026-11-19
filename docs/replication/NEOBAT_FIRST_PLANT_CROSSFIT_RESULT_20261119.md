# NeoBat original plant DOI: first Colombia country-excluded transfer pilot

Date: 2026-11-19. Frozen before original response-outcome fit:
`NEOBAT_COUNTRY_EXCLUDED_PLANT_SDM_PILOT_FROZEN_20261119.md`.

Synthetic known-truth and source leakage tests passed [Actions #44533032332](https://github.com/zuizui0223/esdm/actions/runs/44533032332).
One-shot original 367,988-plant source, original WorldClim BIO1/BIO12 and elevation source validation plus Colombia-heldout regression passed [Actions #44533154427](https://github.com/zuizui0223/esdm/actions/runs/44533154427).
Original plant ZIP SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b` and climate `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf`, elevation `6a9f4e9a37f289d594ed1567b63be344a4dacf247f0b69756e81df031087e3bd` verified and all strict original plant country-cell counts replayed.

## Held-out plant source rank AUCs (exploratory only)

| Pre-fixed source plant | Train focal observed cells | CO test focal observed cells | CO other-plant background cells | AUC BIO1/BIO12/elevation only | AUC + other-plant observed taxa count (source effort proxy) |
|---|---:|---:|---:|---:|---:|
| *Cecropia obtusifolia* | 249 | 21 | 623 | **0.526** | **0.736** |
| *Ficus insipida* | 235 | 79 | 566 | **0.499** | **0.783** |
| *Piper aduncum* | 304 | 61 | 583 | **0.505** | **0.847** |

The fixed three sentinel species were all evaluated; no stop, no outcomes used for switching taxa or country; no Colombia source occurrence entered model training or scaler and no training 25km cell intersected the heldout country. Reported background is NOT verified absence. Near-shore WorldClim nodata cells were excluded according to the frozen rule, with counts in `neobat/plant_colombia_crossfit_pilot.json`. Predictions are **not** calibrated presence probability.

## Substantive interpretation and failure-mode flag

1. The climate/elevation-only predictor provides *essentially no heldout discrimination* for the three sentinel taxa against the sampled other-plant targetgroup background.
2. AUC rises when incorporating `log1p(number of other accepted plant taxa with GBIF observations in the cell)`. This derived covariate is **not an independently measured collection/survey effort**, and can capture plant richness, region/source selection, and correlated observer activity. Its apparent predictiveness could be a measurement artifact, not physiological habitat suitability or resource biomass.
3. The large gap between the two models is therefore a **warning, not an empirical validation of ecological plant suitability**. Do not extrapolate a successful 106×17 plant SDM, or insert these raw rankings into bat M3 as causal resource distributions. The model's most predictive variable may merely reconstruct GBIF plant reporting patterns.

## Next fixed diagnostic (distinct exploratory analysis)

Run a newly frozen **effort-only** score with this same covariate, compare to `abiotic+effort`, and inspect a *heldout source-effort matched* conditional rank test with other-plant taxa count matched between focal presence and background. If effort-only already explains almost the entire gain and climate fails under matched targetgroup recording intensity, the plant predictor needs a different independently estimated detection-bias strategy before a full M3-versus-M1 comparison. Regardless, source-country effects and 1970–2000 climate versus 2000–2025 GBIF temporal mismatch remain.

No bat M0/M1/M3/N1 ranking evaluated; the original 255-plant v1 inference remains frozen and unestimated. No raw GBIF records, coordinates, raster pixels or per-cell predictions in repository.
