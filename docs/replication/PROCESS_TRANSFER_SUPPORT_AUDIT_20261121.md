# Process-component transfer input-support audit (2026-11-21)

**Status: new reusable source-independent diagnostic, illustrated retrospectively on already frozen aggregate field data. No new empirical fit or scientific claim.** The production baseline and original E4/E5/E7/R5b results remain unchanged.

## Motivation

v0.4-R5b used a directly calibrated state channel and passed all 16 known-truth transfer replicates. The E4 empirical transfer is a different outcome: full minus activity-knockout heldout log-score = **-0.6390511804**, whereas full minus state-knockout = **+0.0083909250** (exploratory). The earlier post-result audit reported that eastness-z training support **[-0.9395454272, 1.6528810931]** and eastern holdout **[3.1950123640, 8.4895977440]** do not overlap. Moreover, the D-prefix heldout observational source, accounting for ~99% of heldout focal events, was not observed in the training StateAnnotatedCount source domain; camera registration was assumed perfect in that annotated stream, not independently calibrated. These facts are compatible with multiple explanations, not proof of a causal protocol or eastward biological effect.

## Implemented

The response-blind function **audit_process_transfer_support** at src/esdm/transfer/support.py checks three *necessary*, non-outcome input conditions:

1. Each fixed target feature's minimum and maximum lie within the corresponding training feature's minimum and maximum. Missing features and nonfinite or reversed bounds stop. Separate one-dimensional support is not proof of multivariate overlap.
2. Every target physical observation-source domain was represented in training. A new domain requires independent review; the source label itself is not a causal mechanism.
3. Independent observation calibration was explicitly supplied. Model-imputed perfect detection is **not** independent calibration.

It returns **INPUT_SUPPORT_ONLY** (never predictive confirmation), **TRANSFER_INPUT_NOT_QUALIFIED**, or **NOT_EVALUABLE**, with immutable reason codes. Inputs contain only training/target feature supports, source-domain labels and an explicit calibration flag. The function never accepts outcome labels, posterior coefficients, scores or species observations. It cannot choose a better-fitting model or turn an exploratory result into a heldout confirmation.

Tests cover support limits, missing data, unacceptable bounds/domains, source changes and calibration absence. A separate test uses the already archived aggregate E4 covariate/source JSON to reproduce the conservative **TRANSFER_INPUT_NOT_QUALIFIED** decision, including D/NL source-domain novelty; this is a **post-result illustration**, not an independent prediction or rerun of E4 wildlife responses. No E4 scientific threshold is adjusted.

## Research prioritization

Stop treating more fits of the same uncalibrated GBIF-based proxy as ecological validation. NeoBat's frozen 49-fold source-geography shadow reported S3-S1 mean AUC = **-0.00569**, but its plant component is climate-predicted GBIF reporting, not measured fruits. The original 255-plant M3-M1 / rewired-N1 comparison is still **unfitted**.

For regional independent *plant* evidence, use distinct field vegetation plot sources, not the 2026 BCI single-locality census as evidence of broad transfer. Official sources document **BIEN 4.2: 363,258 vegetation plots, 17,247,823 plot-origin observations** (only the plot component is eligible; exclude GBIF reuse) and **sPlotOpen: 95,104 plots from 105 sources and 114 countries**. The three sPlotOpen ~50,000-plot panels overlap substantially and cannot be counted as three independent replications. Tree cover or stem density is not ripe fruit supply. Public descriptions: https://bien.nceas.ucsb.edu/bien/biendata/ and https://www.idiv.de/research/projects/splot/splotopen-splot/ .

The next **genuine new biological test** must freeze independent training and target units with measured calibration and a crossed source-by-geography design before species outcomes are inspected. Compare abiotic/spatial baseline versus state-only, activity-only and full models on identical target units, and report every missing-data stop. This software gate is an input-risk screen, not evidence that a process layer improves out-of-region prediction. All original one-shot study endpoints remain closed.

## Scope

This research branch does not touch main, original response records, model backend, model likelihood, source names, scores, thresholds, or prior one-shot workflows. It does not authorize reopening blocked E3/E4/E5/Clare/MC1 sources.
