# NeoBat exploratory shadow-model country transfer: fixed 51-fold climate-only M1/M3 diagnostic

Date: 2026-11-19. **A deliberately weaker, exploratory *shadow* model family**, not the frozen ecological `M0/M1/M3/N1` from `NEOBAT_M0_M1_M3_PREDICTIVE_BENCHMARK_CONTRACT_20261119.md`. It cannot demonstrate causal plant resource availability, independent plant occupancy, forest structure, survey effort or general feeding behavior.

## Why this distinct experiment is necessary

The full 106×17 plant source-record AUC audit showed that botanical GBIF reporting intensity is a major predictor (country-equal additional abiotic AUC +0.0254 only). Therefore **do not** feed source-record intensity into plant resource maps and call it fruit supply. The fixed v2 106-plant prefit audit then identified **51/84 original bat×country source candidates across 15 bats and 11 countries** for which all 106 outcountry botanical models can be trained after raster no-data exclusion. Original 255-plant v1 remains unestimated.

This *shadow* diagnostic asks only: **Does the published identity of fruit-linked plants add predictive information about a bat's GBIF reported 25km-cell geography beyond the same climate/elevation fields and the mean 106-plant climate-derived suitability proxy, and beyond degree-preserving literature-link rewiring?** The result, positive or negative, is **not** a validated trophic SDM.

## Immutable original sources and denominator

- **Bat** GBIF original DOI `10.15468/dl.nxu727`, 85,912 records, exact source ZIP SHA `fc94ff92a127ec22655733a0b0cdaf12b5b24794fcc0129532e8a1e49fe856f0`.
- **Plant** original DOI `10.15468/dl.xwc5zf`, 367,988 records, ZIP SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`.
- Pinned WorldClim BIO1/BIO12 10' source ZIP SHA `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf`; WorldClim elevation 10' ZIP SHA `6a9f4e9a37f289d594ed1567b63be344a4dacf247f0b69756e81df031087e3bd`. Baseline 1970–2000, GBIF 2000–2025.
- Fixed 106 original source names SHA `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`; 84 original frozen bat×country folds. Source-only `full106_raster_trainability_gate.json` identifies the 51 eligible and gives **no biology outcome**. No outcome-based additions to this fixed 51.
- Published original NeoBat author records and all 200 site-publication embargoes pinned at commit `d25292d19be32a85a21c60384a3f2d818e8081de`. Exclude any literature reference appearing at a site in withheld bat country, even when linked fruit is recorded elsewhere.
- EPSG:6933 **25km** unique strict source cells with known GBIF uncertainty <=12.5km, documented years 2000–2025. All source counts must replay original DOI QC before models. Never treat cells without focal species as independently surveyed absence.

## Model family and negative control, fully frozen

For **each** of the source-qualified 11 heldout countries:

1. Independently fit exactly **106** plant **country-excluded** binary recorded-cell vs source-`datasetKey`-matched other-plant *pseudo-background* models. Same source-matched training rules as completed full botanical reporting diagnostic: positive and background cells require >=1 other GBIF plant taxon recorded in same 25km cell; no heldout-country source rows or cells enter train; >=20 outside-country positive and >=20 source background after raster exclusions. Fit on **three features**: WorldClim BIO1, BIO12, elevation only (training-only `StandardScaler`; `LogisticRegression(C=1,class_weight='balanced',solver='lbfgs',max_iter=400,random_state=20261119)`). **Do not add the test-country source-record intensity to plant models**. If any of 106 training plant models stops, stop *every* bat fold for that country.
2. Evaluate each plant model's model-derived **relative** sigmoid score at every source-audited bat focal and other-bat background cell for that country fold, including test sites, using environmental covariates only. This is NOT observed plant occupancy or local abundance. Compute `B(x)` = arithmetic mean of all 106 scores.
3. Literature links: from pinned NeoBat `Frugivory × Frugivore` only, with complete site-publication embargo for heldout country. Focal `R_s(x)` = arithmetic mean of **all** outcountry-source documented partners among the 106 fixed plants. Require >=3 distinct partners from >=2 original refs; the previously frozen stricter *local recorded partners* source gate must also pass, and all heldout bat folds remain in the 84 denominator.
4. Bat heldout response: focal observed strict bat 25km cells vs observed *other-bat* target-group background in exact same 26-bat universe; within each country, remove focal-positive cells from background. Train on other 28 countries, holdout target country, eliminate any overlapping 25km test-country/source cell from training. Fit only if post-raster >=20 positive + >=20 background outside and >=5 positive + >=5 background inside. Both groups are source *recorded* cells and background is **not verified absence**.
5. Primary **shadow** contrasts, fit on exact same training/test bat cells for all versions using the existing fixed `_ridge_logit_auc(...,reg=1.0)` core and training-only transforms:
   - `S0`: temperature + precipitation + coarse elevation.
   - `S1`: S0 + generic 106-plant **climate-derived relative score** `B(x)`.
   - `S3`: S1 + actual source-published fruit partner relative score `R_s(x)`.
   - `SN1`: S1 + degree-preserving edge-rewired outcountry literature fruit partner score `R_s^{swap}(x)`.
   - **Primary exploratory** `S3-S1` and `S3-mean(SN1)`, with a fixed 99 rewiring draws and same bat source responses, controlled predictor dimensionality and training sample. Degrees of bat and plant preserved; changed focal partner set required, otherwise STOP. The original frozen ecological M3−M1/N1 statistics remain **unestimated**.
6. No forest, topographic ruggedness, independently measured botanical/animal effort, fruiting phenology or 3D realized feeding data enter this shadow model. Source-derived climate-only plant scores can make S3 a nonlinear transformation of climate; any positive result may be an algorithmic/compositional proxy, not a mechanistic trophic response.
7. Report all **84** original bat×country statuses and all source STOPs; all 51 prequalified remain accounted for. For fit-qualified folds report AUC S0/S1/S3/SN1, both signed deltas, 99-draw null upper-tail, per-country and per-species descriptive means, **not row-wise independent-study p-values**. No tuning based on heldout results or retrospective cohort selection. A source model with no deterministic N1 focal partner variation fails closed.
8. All raw DOI ZIPs, exact coordinates, 25km cell IDs, model predictions for cells, bat/plant source `datasetKey`, survey/event IDs and source rasters stay **in Actions RAM/temp only**. GitHub artifacts and commits contain only aggregated bat×country effects and counts, original SHA pins and STOP status.

## Interpretation and stop

Regardless of whether S3>S1 or S3>SN1, this is **exploratory source-geography link-identity discrimination, not real resource-dependent SDM**. Retain original 255-plant v1 result as missing/unestimated. A confirmatory independent ecological claim would require calibrated independent plant/resource availability, 17-country forest/terrain and true effort controls, source-independent holdout observations and ideally observed feeding linkage.
