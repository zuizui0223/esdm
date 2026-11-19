# NeoBat exploratory v3 fixed35 source-disjoint post-raster trainability — frozen before results

Date: 2026-11-19. Target: `zuizui0223/esdm` research branch, **not main**. This is a source/raster *input* audit, no plant ecological validation and no bat M0/M1/M2/M3/N1 fit.

## Predeclared cohort and source IDs

- **35** sorted plant species selected by cross-country original GBIF `datasetKey` source-training support alone, frozen in `docs/replication/neobat/v3_source_disjoint35_partner_gate.json` with name SHA-256 `5f6ee54473b074b2b5329b1ddd9cc966e739f4f12b93db75154ce59a9f7b92ee`.
- The **same 17** country holdouts, exactly **35×17=595** plant prediction training evaluations; preserve all positives, negatives, source failures, and missing-raster stops. The original **84** bat×country input denominator, 66 literature/N1-qualified and 63 additionally bat background qualified, is retained unchanged and never outcome-selected.
- Original 367,988-row GBIF plant download `10.15468/dl.xwc5zf`, ZIP SHA256 `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`, original accepted 255 concepts and original 25km EPSG6933 strict species-country cell counts. Re-download only the already minted archive; **NO authenticated GBIF POST**. Collect every `datasetKey` in withheld country's original 2000–2025 plant records **including unknown-coordinate-uncertainty** and embargo globally from all training countries.
- Original WorldClim v2.1 BIO1/BIO12 10 arc-minute 1970–2000 source ZIP SHA256 `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf`; independent WorldClim elevation ZIP SHA256 `6a9f4e9a37f289d594ed1567b63be344a4dacf247f0b69756e81df031087e3bd`. These are climatology and coarse elevation; not forest structure, annual fruit production, or resource biomass.

## Locked source and raster sampling

For each of 595 plant×country folds:

1. Build plant sources with original 25km unique recorded cells and original country/dataset key; each qualifying source-`datasetKey` context must have >=1 focal plant cell and >=1 other plant taxon cell in that country.
2. For the training set, **exclude all botanical datasetKeys touching heldout country** in any original plant row (even if low precision); exclude every 25km grid cell known from the heldout country's precise plant occurrences, including cross-border cells. Compute source-observation intensity `log1p(number of different OTHER accepted original plant taxa)` **only** from unembargoed outside-country sources.
3. Require >=1 source-recorded other plant taxon in the **same cell** for both plant-positive and background roles, using original 255 accepted plant taxa (not just the selected 35). The source background must contain no observed focal plant cell from any original dataset. Missing focal observation is **not a verified absence**.
4. Create heldout-country source-matched positive/background record cells using the prior original source method (no heldout training), with the same per-cell other-taxon criterion. These are only source input *quantity* diagnostics, not performance test samples.
5. Sample BIO1/BIO12/ELEV from the original source TIFFs at the 25km EPSG6933 centroid, using original `extract_environment` and strict nodata filters. Record raw source quantity and post-raster positive/background cell counts and excluded cell totals. A coastal centroid falling in NoData is a technical source STOP, not biological absence.
6. Require >=20 outside-country **raster-valid** plant positive cells and >=20 outside-country other-plant pseudo-background cells; report training-source qualified as `true` only if **both** pass. Heldout source AUC *potential* additionally requires >=5 positive and >=5 background **raster-valid** country cells. Do **not** fit plant models, choose thresholds or calculate heldout AUC in this stage.
7. Verify every pair already satisfied the earlier global source-disjoint pre-raster 20/20 gate and that new post-raster counts cannot exceed corresponding source-only retained cell counts. Require exactly **595** unique pairs, 35 names, 17 countries; never select a different plant pool after these results.
8. Report country-level number of all 35 trainable, number of heldout test-scorable, and globally trainable species across all 17. Intersect **without selection** with the fixed 84 bat fold roster and prior 35 literature+N1+bat-source gates (63 folds), preserving 84 as denominator. **Source-disjoint35 raster training gate is a new test; old 106 raster passes cannot stand in.**
9. Keep raw species×cell tables, GBIF dataset IDs, event identifiers, coordinates, original GBIF rows, and original raster pixel matrices off GitHub/Actions artifacts. Export only aggregate per plant×country and bat×country counts and status flags.

## Interpretation ceiling

Even if 35/35 plants are trainable in some countries, the source-recording intensity covariate remains a mix of true botanical richness and GBIF reporting/collection effort. Separate source datasets are not fully independent institutions or surveys; no resource abundance, fruiting/feeding, ecological population niche or bat source-linked M3 superiority is established. Real botanical source-bias-calibrated relative suitability predictions, country-wide independent forest and targetgroup effort, paired bat M0/M1/M3/N1 AUC and an external unopened validation period/source are still missing.
