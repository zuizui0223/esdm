# NeoBat trophic SDM — phase 1 design (DRAFT, response-blind)

Date: 2026-11-19  
Status: **design only, not an empirical result, not a validated/frozen fit**  
Scope: New Neotropical frugivorous-bat 2D predictive benchmark, separate from frozen E4/E5/E7 and `batter` evidence. Do not modify or reinterpret those outcomes.

## 1. Question and estimand

Does independently established **fruit-consumption partner identity** improve the *spatial transfer of bat occurrence relative suitability* above (a) abiotic/habitat predictors, (b) total predicted availability of the same plant pool, and (c) randomized interaction links?

The estimand is the paired gain in held-out, target-background-conditioned **presence ranking**, averaged with equal weight across eligible bat species and independent geographic folds. **Not** absolute occupancy, population density, effect of fruit consumption, or reciprocity.

## 2. Source registry (verify original bytes, license, taxonomic schema, geographic independence)

1. **Observed bat–plant interactions**: Florez-Montero et al. 2022, *Ecology* 103:e3640, `https://doi.org/10.1002/ecy.3640`, publisher supplementary DOI `https://doi.org/10.5281/zenodo.4894176`. **Author-origin supplemental data independently verified** at `https://github.com/gflorezm/NeoBat_Interactions`, with GitHub blob-identical mirrored CSVs at `https://github.com/globalbioticinteractions/NeoBat_Interactions`. **Actual CSV denominators:** 2,571 total interaction rows (**1,931 Frugivory** and 640 Nectarivory), 200 study sites, 169 references; fruit rows cover 110 sites / 104 references. The paper additionally reports 93 bats and 501 plants overall; these species counts must **not** be mixed with filtered raw-name counts. The source tables and column schema have been read; hashes and data-quality receipts are in `NEOBAT_PHASE1_SOURCE_PREFLIGHT_20261119.md`. The archive from Wiley/Zenodo could not be retrieved via the tested web access path, so **byte identity to that archive remains unverified**. Source rows represent interaction reports **not** non-detections, standardized abundance or independent occurrence events. Study/site ID, coordinate precision and sampling method must be accounted for. Explicit accepted-name crosswalk and external response data still required.
2. **Bat response**: independent GBIF DOI-bearing bulk occurrence download (`https://techdocs.gbif.org/en/data-use/api-downloads`) of accepted Phyllostomidae bat taxa; collection date 2000–2025; species identification, valid coordinates, explicit coordinate uncertainty, provenance/dataset key, de-duplication and study-footprint exclusion. Presence-only; no pseudoabsence treated as verified absence.
3. **Plants**: independent GBIF DOI-bearing occurrence download of partner-plant pool; use spatially cross-fitted plant SDMs. Original taxon names and synonyms mapped to frozen accepted taxon IDs. Genus-only identifications excluded from species-level primary network; sensitivity at genus level pre-specified.
4. **Environmental baseline**: CHELSA v2.1 (thermal, water, seasonality), forest/land-cover fraction and topography from documented rasters at harmonized resolution, and fixed sampling-bias controls. Reuse `sdmr` predictor-universe lesson, **not** its blocked empirical Product-B claim.
5. **Independent corroboration**: Dryad `https://doi.org/10.5061/dryad.cvdncjt76` has separate bat–plant pollination matrices and traits; do **not** mix pollination/nectarivory into primary fruit resource. Reserve for future nectarivore extension. Bat Eco-Interactions (`https://batbase.org/`) can be assessed for independent link coverage, with overlap by citation fingerprinted.

## 3. Spatial/temporal unit and eligibility — frozen before viewing response patterns

- Initial 25-km equal-area grid across Neotropical mainland and nearby islands; 50-km resolution robustness. All cells joined in equal-area projection. No random occurrence-level splitting.
- Primary phenology-neutral baseline: link from historical literature treated as potential partner identity (not temporally realized fruit abundance). Do **not** label modeled suitability as fruit availability or consumed biomass. Phenology is a later data-dependent module, requiring season-specific measurements.
- Candidate focal taxa: frugivorous Phyllostomidae with accepted species names in BOTH NeoBat and independent bat occurrences; include all eligible taxa, not only charismatic exemplars.
- Provisional pre-response feasibility gate: >=5 eligible bat species and >=4 independent outer regional groups; each focal species >=20 distinct 25-km positive cells in training, >=5 in its tested region(s), >=3 taxonomically resolved fruit partners from >=2 independently identified study/site sources in training. If impossible, report `DATA_INADEQUATE` and do not relax gates after opening held-out bat responses. Counts are **design thresholds**, not claimed coverage.
- All records from one underlying publication/site/event stay in the same fold; group by study and geographic region. Detect and exclude event-level reuse between interaction sites and bat response records.
- Interaction record frequency is **not a measured diet proportion**; primary links are binary. Historical/temporal mismatch flagged; sensitivity by temporal strata only if sufficient data.

## 4. Nested predictive architecture

For bat species s and grid cell i, estimate a *relative* observation intensity with bat sampling effort controlled using **target-group background** rather than unverified absences:

`log lambda_obs(s,i) = f_s(climate_i, forest_i, topography_i) + u_s(i) + alpha_s + delta_s B(i) + gamma_s R_s(i) + observation-effort term`

`p_hat_k^(-fold)(i)`: plant k relative suitability from plant model trained **without the outer held-out region**. Because presence-only plant data lack calibrated absences, this is *not* a calibrated P(plant present).

`B(i) = mean_k p_hat_k^(-fold)(i)` (predicted partner-pool plant availability proxy / background richness-like baseline).

`w_sk = 1[# independent frugivory link s-k observed in TRAINING NeoBat sources] / (# partners for s in training)`.

`R_s(i) = sum_k w_sk p_hat_k^(-fold)(i)` (interaction-specific resource-alignment score).

Use within-fold standardization; common environmental functional form, same spatial field complexity and sampling-effort handling across all models. Spatial term `u_s` fitted to training only, not reconstructed from held-out presence locations. Species coefficients hierarchically regularized; resource effects unconstrained in estimation, direction tested rather than forced.

**Causal boundary**: `gamma_s` is a predictive association conditional on supplied covariates; even with observed dietary links this is not the causal effect of plant abundance on bats.

## 5. Predeclared model ladder

| ID | Predictors added to shared environment + spatial + observation baseline | What it tests |
|---|---|---|
| M0 | none | Abiotic/land-cover/effort baseline |
| M1 | B(i), unweighted predicted plant-pool suitability | Generic vegetation/plant richness proxy |
| M2 | R_s(i), observed training links | Link-specific pattern without richness adjustment (diagnostic) |
| **M3** | **B(i) + R_s(i)** | **Main test: link-specific resource alignment beyond generic plant pool** |
| N1 | B(i) + R_s^rewired(i) from training-only degree-preserving bipartite swaps | Does exact identity outperform matched false links? |
| N2 | B(i) + nonpartner plant score matched on habitat/climate and sampling coverage | Does shared habitat alone explain extra prediction? |

Primary contrast = M3 minus M1, conditional on N1/N2. Preserve bat and plant degree sequences in bipartite rewiring, restrict to biologically/geographically eligible candidate plant pool, and carry training-only estimated partners to outer test. Use >=199 fixed-seed null swaps per eligible fold if feasible. Same model complexity/regularization and effective plant measurement effort in M3 and nulls; otherwise flag incomparable.

A positive M3-vs-M0 alone is **insufficient**; plant richness or sampling geography might explain it.

## 6. Information barrier and evaluation

1. **Preflight** *without opening held-out outcomes*: verify source file bytes, licenses, field mappings, accepted names, spatial precision, source overlap, record counts/regions and model-fit feasibility. Publish hashes, eligibility denominator, exact folds and exclusions. STOP on missing schema or insufficient units.
2. **Discovery/training**: nested spatial blocked fitting and predictor tuning, 250-km minimum nominal block spacing where geography permits; group publication/site IDs; independent target-group biased background from similarly recorded Chiroptera. Spatial block + country/biome labels are frozen; no test-point model selection. On the test region, no bat responses, plant occurrences or network records may influence environmental selection, plant fits or link weights.
3. **Final held-out test**: evaluate outer region/country folds with fixed candidate and candidate-independent evaluation background. Main score = paired difference in presence-ranking of withheld bat presences versus matched test-region target-group background; species and outer folds receive equal weights, with uncertainty resampling whole regions/studies, not individual records. Secondary: held-out point-process/conditional logistic log-score **only if exposure/background process is defensible**, and spatial transfer calibration where verified absences exist. Do not use naive Brier or call raw predictions occupancy probabilities.
4. **Decision rules**: predictive support only if M3-M1 region-block bootstrap 95% interval lower bound >0, observed improvement exceeds 95% of same-complexity degree-preserving null improvements, and results are not determined solely by one country/species. Otherwise label `NOT_SUPPORTED` (valid assay), or `INDETERMINATE`/STOP (data/assumption deficit). Report signed per-species and per-region effects regardless of aggregate.
5. **Sensitivity**: 25 vs 50 km; target-group background variants; training only vs country-excluded network links; binary versus effort-standardized weight (if study effort actually known); removal of Ficus/Piper/Cecropia high-link plants; source publication/citation dedup; varying spatial fields; phylogenetic/species partial pooling. Strictly distinguish planned sensitivity from confirmatory primary decision.

## 7. Observation/confounding audit

- Plant and bat GBIF records co-concentrate at accessible sites: carry common sampling-density proxy, source exclusion, target-group background and independent holdout.
- NeoBat study links have unequal study effort, and historical records may not reflect currently usable resources: binary links are **potential partners**, not verified local food abundance.
- The model estimates plant species distribution, not fruit crop, phenology, vertical stratum or local encounter. A positive result cannot establish consumer foraging mechanism.
- Local range boundaries and missing plant occurrences can bias zero resources; avoid interpreting no record as absence; propagate plant-SDM uncertainty by cross-fitted draws/ensembles, with shared folds.
- Relative likelihood is not calibrated occupancy. Historical network source size is not sample size for bat distribution.
- No simultaneous consumer–consumer competition coefficients from co-occurrence; these are not identifiable as interaction effects (Blanchet et al. 2020, DOI 10.1111/ele.13525).

## 8. Deliverables and claim ladder

A. Provenance manifest: input URLs, hashes, snapshots/GBIF DOIs, licenses, taxon crosswalk, normalized field schema and exclusion ledger.

B. Eligibility & observability report: studied taxa × independent source/study/region, spatial cells, study overlap, valid training/test folds, measurement-effort gradient. This is the **first executable empirical gate**.

C. Frozen analysis manifest: same folds and predictors for M0/M1/M2/M3/N1/N2; no modifications after held-out opening.

D. Prediction and uncertainty: withheld-region per-species ranks/differences and comparison to degree-preserving null, with regional bootstrap intervals.

E. If predictive support: manuscript claim is **"independently documented plant-consumption links improve out-of-region bat distribution prediction beyond abiotic environment and generic plant availability"**. If not: no forced biological support.

## 9. Phase 2 and phase 3 extensions (not phase-1 claims)

- Phase 2: `P(z | x,t,s, individual)` learned from independent altitude/acoustic observations with explicit detector error, leveraging `batter`'s individual-level variance/shape hierarchy; do not infer height from plant SDMs alone.
- Phase 3: independently classified commuting/foraging states, resource phenology, conditional movement/SSF and matched consumption/behavior observations to distinguish shared environment versus mechanistic resource choice. Only these can support stronger behavioral claims.

## References

- Florez-Montero et al. (2022), *Ecology* 103:e3640. `https://doi.org/10.1002/ecy.3640`
- Phillips et al. (2009), *Ecological Applications*, presence-only sampling-bias and target-group background. `https://doi.org/10.1890/07-2153.1`
- Blanchet, Cazelles & Gravel (2020), *Ecology Letters*, co-occurrence is not evidence of interactions. `https://doi.org/10.1111/ele.13525`
- GBIF occurrence download API: `https://techdocs.gbif.org/en/data-use/api-downloads`
