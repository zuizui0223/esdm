# NeoBat CO three-plant identical-test cross-dataset refit — exploratory empirical result

Date: 2026-11-19. This is a **post-hoc source robustness diagnostic** on an already opened botanical GBIF discovery cohort, not a new ecological validation, ecological M3–M1 or source-independent resource abundance.

## Verified execution and replay

- Pre-outcome protocol: `docs/replication/NEOBAT_CO_3PLANT_CROSS_DATASET_TRANSFER_FROZEN_20261119.md`.
- Source-free original-shaped tests PASS: [Actions #44542600875](https://github.com/zuizui0223/esdm/actions/runs/44542600875).
- Original plant DOI and source climate/elevation ZIP re-verification, **all original three Colombia source-matched AUCs and source cell denominators replay exactly**, then training source-disjoint refit PASS: [Actions #44542764573](https://github.com/zuizui0223/esdm/actions/runs/44542764573).
- Aggregate receipt: `docs/replication/neobat/CO_three_plant_disjoint_source_AUC.json`.
- Original plant download `10.15468/dl.xwc5zf`, 367,988 records, original SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`; WorldClim BIO1/BIO12 ZIP `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf`, elevation `6a9f4e9a37f289d594ed1567b63be344a4dacf247f0b69756e81df031087e3bd`. All 706 original dataset keys present in CO were forbidden globally from training. No raw source keys or grid cells persisted.

## Same original heldout Colombia cells; refit changed only training source scope

| Fixed plant | New source-disjoint training focal/background cells | Original heldout positive/background cells (unchanged) | Original combined AUC | Source-disjoint combined AUC | **Paired AUC change** | Abiotic-only AUC after source embargo | Extra abiotic AUC over source-intensity only after embargo |
|---|---:|---:|---:|---:|---:|---:|---:|
| *Cecropia obtusifolia* | 35 / 565 | 21 / 525 | 0.7318 | **0.7420** | **+0.0102** | 0.5718 | +0.0323 |
| *Ficus insipida* | 96 / 661 | 78 / 504 | 0.7667 | **0.7727** | **+0.0060** | 0.4694 | −0.0221 |
| *Piper aduncum* | 62 / 650 | 61 / 521 | 0.8393 | **0.7729** | **−0.0665** | 0.4837 | −0.0708 |

All three passed the original >=20 positive/target-background training and >=5 test-cell class thresholds after original raster nodata exclusion. The training `log1p(other species recorded in a cell)` covariate was recomputed *only from nonembargoed source datasets*. The test source and its original intensity column were unchanged; **source-intensity-only AUCs therefore remained exactly the same** (0.7097, 0.7948, 0.8436), but this does not indicate source-independent biological plant habitat or measured survey effort.

Original post-embargo exact-intensity conditional AUC was 0.701 / 0.491 / 0.521, but only 5.49% / 4.31% / 2.95% of all possible heldout focal-positive × pseudo-background pairs had exactly matching source-intensity counts. Such small eligible subsets cannot establish a general conditional effect.

## Scientific ceiling and next gate

The paired result demonstrates **heterogeneous sensitivity to overlapping GBIF source datasets** under exactly the same heldout plant recorded-cell population. Even after source embargo, the botanical *recording-intensity proxy* predicts heldout GBIF source recording much better than climate/elevation-only for two of three sentinels. The only plant with a clear paired source-embargo reduction is *Piper aduncum*; no universal source leakage direction should be inferred from only three preselected taxa.

This does **not** establish true occurrence, presence-absence, fruit production, food-resource availability, bat feeding, ecological M1/M3 superiority or independently repeated field sampling. The source-disjoint **106 plant** set cannot be trained in full in any of the 17 country holdouts; only **35** of the 106 names have adequate strict source-disjoint training input across every holdout. The original 255-plant primary benchmark and main remain unmodified and unestimated.

**Next input-only step:** derive the single fixed 35-name globally source-disjoint plant universe *from the 1802-fold source-only receipt* and audit how many of the original 84 bat×country folds still retain >=3 author-documented frugivory partners, >=2 independent original NeoBat references, and a structurally possible focal-specific degree-preserving N1 swap. Keep the original 84 denominator and preserve every exclusion. Do not claim 35-plant ecological success or select source-cohort species based on AUC.
