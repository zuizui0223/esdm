# C1: Independent Asian mammal camera-study turnover — frozen analysis design

**Date:** 2026-11-17 JST. **Status:** FROZEN_BEFORE_CAPTURE_RESPONSE_OPENING.

## Motivation and independence

The Safari14 result (PR #232) supports *recorded* park sorting against a camera-level fixed-degree exchangeability null, but cannot identify geographic source pools, environment or detection. PR #233's three public landscape-pair examples were selected after seeing the response. Their signs may be misleading. A new tropical Asia study-level network allows a completely separate *predictive* evaluation of environmental versus geographic explanation without carrying Safari14 species or ecological signs forward.

Data: Mendes et al. (2024), CamTrapAsia (Ecology 105:e4299), https://doi.org/10.5281/zenodo.10780971 (Zenodo record 10780971, version 1). Public webpage reports 239 tropical Asian camera-trapping studies, 232 mammal species, 876,606 camera trap-nights. **Use only** `CamTrapAsia_Metadata_20231031.csv`, `CamTrapAsia_Captures_20231031.csv` and `Species_Traits_20231031.csv` from the SAME Zenodo record. These have published MD5 hashes `2b50c534737b0c98a93da54128b10a32`, `a73975d7626def4012a4e1197497ba87`, `59e0748f8aaf59b23b936248f1e63fc9`. SHA256 of retrieved bytes also archived before calculations. No image downloads. Public exposure metadata `survey_id,country,landscape,effort,n_cameras,Y_lat,X_long,forest_cover_20km,temperature_20km,precipitation_20km,human_footprint_20km` were known before outcome opening. Source contains publications from several observers, not an independently calibrated camera detector, and regional species pools differ.

### Focal question

Does **environmental distance (IBE)** improve out-of-landscape prediction of *recorded mammal species replacement* beyond **geographic distance (IBD)** and sampling effort?

This is a test of *incremental predictive information* for a spatial community pattern. Even a positive result would not establish evolutionary adaptation, dispersal causality, source-pool accessibility or eSDM model superiority.

### Frozen extraction and sampling

1. Metadata must have exactly one row per nonblank `survey_id`. Select studies with **`effort >= 500 trap-nights` and `n_cameras >= 10`**, valid lat/lon and all four finite 20-km environmental covariates. A scientific or technical schema failure stops the one-shot attempt, without threshold rescue.
2. Captures join on exact `survey_id`. Mammal status must be established by a published mammal class or unambiguous species-to-mammal mapping from the published traits table, never by a handpicked list of favorable taxa. Retain only species-level identities and independent-record totals of **at least 2 per species per study**. Deduplicate study × species; no image counts used as independent replications. If the capture data do not contain interpretable independent-record totals and species-level mammal identification, terminal **RESPONSE_SCHEMA_STOP**. Column aliases may be mapped based on header names, but selection rules and biological thresholds may not change.
3. A study is analyzable only if at least **five mammal species** survive threshold (2); no substitutions or pooled taxa. Single-country geography is not a hard stop because this is an independent regional observational dataset, not E5's G3/G4/G6 programme.
4. For any distinct eligible study pair, compute Baselga Simpson turnover: `beta_sim = min(b,c) / [a + min(b,c)]`, with `a` shared species, `b,c` exclusive species. If denominator is zero, mark unestimable and exclude by fixed rule. Geographic distance = great-circle haversine in km using published study centroids; no invented barrier lines or geocoding.
5. `landscape_group` is exact `(country, landscape)` from metadata. Assign all rows in a landscape to the SAME split using a deterministic SHA256 of `C1-20261117|country|landscape`: first byte `< 51` (~20%) = validation; otherwise discovery. Never adjust split on outcome. Analysis stops with `INSUFFICIENT_TRANSFER_SUPPORT` if fewer than 30 eligible studies/8 landscape groups in discovery or fewer than 12 studies/4 landscape groups in validation, or fewer than 100 estimable pairs in either.

### Baselines and predictive decision

For each pair, nuisance covariate is `abs(log(effort_i/effort_j))` (effort ratio), geography is `log1p(km)`, and environment is standardized 20-km Euclidean difference in exactly four covariates: forest cover, precipitation, temperature and human footprint. Environmental feature centers and standard deviations are estimated from *discovery studies only*, with zero-variance features contributing exactly zero. The distance and effort pair predictors are centered and standardized on discovery pairs only. Outcome is a continuous bounded dissimilarity; predictions are clipped to [0,1].

Baseline `G`: intercept + geographic distance + effort-ratio. Full `G+E`: baseline + environmental distance. Use fixed ridge penalty alpha=5 on **non-intercept** coefficients, with intercept unpenalized. Fit on **discovery-with-discovery pairs only** and calculate heldout absolute error on **validation-with-validation pairs only**, with no cross-split pairs involved in fitting or scoring. Every eligible pair is retained; pairs are not statistically independent and the measured numerical gain is descriptive only.

Primary `MAE_gain = MAE_G - MAE_G+E` on validation pairs. **Descriptive positive E gain** requires `MAE_gain >= 0.02` and `coef_E > 0` on discovery; otherwise label no evidence of useful incremental prediction. Report signed gain even if negative, withheld study and pair counts, feature distributions, and both coefficients. **No p-value, CI or posterior claim** from pair-level pseudoreplication.

### Secondary non-tuned checks

1. Report heldout MAE differences for eligible same-country pairs and between-country pairs separately, if each contains >=20 valid pairs; do not promote either to primary.
2. Report proportion of discovery and validation pairs with nonzero turnover, median turnover, median geographic km and environmental distance. **No inference of ecological cause** from these marginals.
3. Report realized landscape overlap and shared publication source across partitions using metadata only, without altering the primary split.

### Source/technical stops and claim firewall

1. Reuse only the exact Zenodo record and published MD5 source signatures; 404, 401, hash drift or download redirects into HTML -> `TRANSPORT_OR_SOURCE_STOP`. No alternate source switching or repeated attempt loops.
2. Freeze schema/field selection decisions **before** inspecting captures content; header-only checks are allowed to resolve aliases but cannot change sampling/method thresholds.
3. A result is a **different ecological dataset/test**, not a second Safari14 camera-level fixed-margin result, not an E5 qualified camera detection reference, and not an eSDM cross-geography model fit. E4/E5/E7/E7-C and Safari14 outcomes are immutable.
4. A single source-backed execution may be performed; publish every support failure, negative gain and exception. No response-informed thresholds, new regions, taxon switching, or refits.