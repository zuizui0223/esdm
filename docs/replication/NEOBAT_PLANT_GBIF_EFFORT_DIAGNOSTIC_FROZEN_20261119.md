# NeoBat plant-GBIF source-effort confounding diagnostic (post-hoc, exploratory)

Date 2026-11-19. This is **a post-hoc diagnostic prompted by the already-opened Colombia three-species pilot**. It is not a new confirmatory test, and no third country or sentinel species may be substituted. Original v1 full 255-plant M1/M3/N1 remains unestimated; exploratory v2 106-plant suite not yet fitted.

## Fixed comparison BEFORE opening new diagnostic outputs

Use the exact same three prior preselected sentinels (`Cecropia obtusifolia`, `Ficus insipida`, `Piper aduncum`), holdout CO, 367,988-source-row GBIF plant ZIP DOI `10.15468/dl.xwc5zf`, 2000–2025, known-precision 25km cells, identical source-other-plant pseudo-background and hashed official WorldClim BIO1/BIO12/elevation. Retain the original training-only scaler, `LogisticRegression(C=1,class_weight=balanced,lbfgs)`, country split, all cell inclusion/exclusion, three-column original abiotic model and four-column source-effort model. The original result receipt stays unchanged.

Perform exactly:

1. **Effort-only** (new): `log1p(n_other_plant_taxa_recorded_in_cell)` from the *same test/source cells*, training only outside Colombia; compute heldout target-background rank AUC.
2. **Incremental environment** (new): `AUC(abiotic+effort)−AUC(effort-only)`, to see whether the original 0.74–0.85 apparent advantage was dominated by source covariates. Report original AUCs again unchanged for cross-check.
3. **Exact-effort conditional AUC**: For **each exact** integer number of other plant taxa in the heldout cell, compare heldout positive vs background ranking *only* within that integer group, pooled across groups by number of comparable positive×background pairs (fixed within-stratum AUC). Report the fraction of all possible positive×background pairs that had comparable exact effort, with `null` conditional AUC if no pairs. Compute for both abiotic-only and abiotic+effort models.
4. Sensitivity using fixed non-data-driven effort bins `[1], [2–3], [4–7], [8+]`; similarly report comparable pair counts/fractions and conditional rank AUC for both models. Do not modify these bins if empty or unfavourable.
5. Report `n_other` and dataset sample restrictions explicitly: it is NOT measured search effort, but a mixture of local plant diversity, encounter bias and observer behavior; a coincident other-species record is not independent detection calibration. Do not interpret high `effort-only` AUC as plant habitat ecology.
6. No plant SDM model selection, causal conclusion, bat M3/M1/N1 heldout rank, new GBIF downloads, raw occurrences, protected locations, source cell IDs, or pixel arrays in saved results. Preserve all failures. Even high conditional AUC would remain exploratory and source-dependent.

## Decision criterion (exploratory only)

A small increment beyond effort-only **(<0.02 AUC)**, together with no useful same-effort AUC, would show that the v2 plant baseline is not yet source-robust enough to use as definitive ecological food-resource suitability. This threshold is defined after seeing the original combined AUC, so **is not a confirmatory hypothesis decision**. It is a workflow risk flag, not an ecological null test.
