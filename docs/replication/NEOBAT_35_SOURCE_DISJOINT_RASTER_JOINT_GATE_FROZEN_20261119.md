# NeoBat fixed35 joint datasetKey-disjoint + raster-valid plant training source gate — frozen

Date: 2026-11-19. **Input-only exploratory prefit audit**, no ecological model ranking, genuine feeding resource abundance or independent validation.

## Data and exact prospective decision

The already frozen source-only v3 candidate pool contains **35 plant species** (SHA-256 `5f6ee54473b074b2b5329b1ddd9cc966e739f4f12b93db75154ce59a9f7b92ee`) drawn **only** from global botanical GBIF datasetKey-disjoint training support. It retained 63/84 original bat×country folds under NeoBat author-frugivory refs + focal-degree N1 structural swaps + bat target-group source background. **63 is only a source-quantity upper bound**, because joint source embargo and raster nodata have not yet been applied.

This new test locks **35 × 17 = 595** original plant×country training evaluations, and always retains all **84** original bat×country inputs. No species/country/fold may be swapped based on any previous 106-species AUC. Same original 255-plant v1 and 106-plant v2 contracts remain unchanged.

## Source identity

1. Original GBIF plant DOI `10.15468/dl.xwc5zf`, 367,988 rows, ZIP SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`; full original species×country 25km known-precision source cell counts must replay exactly. Reuse original DOI, no new GBIF POST.
2. Global heldout source embargo `datasetKey` sets from **all original plant records** in withheld country (including precision unknown), as fixed in source35 upstream. Never export dataset IDs.
3. Pinned WorldClim v2.1 BIO1/BIO12 original ZIP SHA `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf` and coarse elevation original ZIP SHA `6a9f4e9a37f289d594ed1567b63be344a4dacf247f0b69756e81df031087e3bd`. EPSG:4326 GeoTIFFs sampled at EPSG:6933 25km cell centroid; nodata/nonfinite explicitly excluded. Climate baseline 1970–2000, not fruit phenology.

## Locked source and raster joint test

For **each of 17 holdout countries**:

1. Exclude *all original botanical GBIF datasets that also have any record in withheld country* from every other-country training source. Do not use these datasets even to compute the *training* `log1p(n_other_plant_taxa_recorded)` field. Plant target-group source context must be reconstructed solely from allowed dataset IDs, as in the successful original Colombia 3-plant cross-source refit.
2. Build training focal observed and source-matched nonfocal botanical target-background cell sets for each of the fixed **35 names**, with both roles requiring at least one recorded nonfocal plant taxon in the same 25km source cell. Exclude every heldout-country 25km recorded plant cell from training, including border overlap. Focal plant records from embargoed datasets are allowed **only as a conservative background exclusion mask**, not positive labels, effort or predictor samples.
3. Extract *all three* originally authenticated WorldClim source values (BIO1, BIO12, elevation) at 25km cell centroid and exclude any cell with an invalid or nodata value. Threshold **>=20 training focal positive cells and >=20 source-matched target-background cells** after this joint source-embargo + nodata filter. Do not infer absences from source gaps. Record distinct original source/rasters excluded counts.
4. Reproduce the three frozen *Colombia* source-disjoint post-raster training quantities from `CO_three_plant_disjoint_source_AUC.json`: *Cecropia obtusifolia* **35/565**, *Ficus insipida* **96/661**, *Piper aduncum* **62/650**. If any number differs, **STOP** the complete 595-grid source gate. This protects the previous no-leakage implementation and masks.
5. Reproduce the original prior **1,802** country source-data selection and exact 35-name derivation (previous source35 source gate); no independent plant AUC or bat rank scores are re-fitted here.
6. Report all **595** original 35×17 plant source+raster-qualified entries and all **84** original bat fold statuses. A bat fold can be flagged 'complete35 joint source+raster **training-input possible**' only if all 35 distinct plant species pass the above training gate in that fold's country AND the previously source-qualified literature-frugivory+N1+bat target-background gates passed. Do not retroactively remove failures or relabel as 35 fitted plant SDMs.
7. Report number of countries with full 35, eligible bat folds/species/countries, number of plant×country training failures and cause counts; compare to prior source-only 63/84 **as a new restrictive input-only gate**.
8. Save only species×country aggregate cell counts/STOP status, country-level aggregate denominators and source hashes; never store raw original GBIF rows, datasetKeys, source IDs, cell IDs, coordinates, WorldClim pixel arrays, individual cell features, fitted predictions, or bat responses.

## Scientific ceiling

No 35 relative plant suitability surfaces, ecological occupancy, fruit biomass, surveyed background absences, observation-independent verification, true feeding, M0/M1/M3/N1 bat AUC, cause of bat social information sharing or 3D resource use is inferred. Even a positive joint training gate only says that an **exploratory source-record botanical model can be fitted** in principle; independent forest, sampling effort and genuinely heldout bat predictions remain distinct.
