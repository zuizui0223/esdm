# NeoBat fixed 51-fold *shadow* source-geography benchmark — empirical result

Date: 2026-11-19. This is a deliberately **weaker climate-only, observational-source diagnostic** and MUST NOT be substituted for the original frozen ecological 255-plant M0/M1/M3/N1 benchmark. Its original fixed model definitions and 84-fold denominator are in `NEOBAT_SHADOW_CLIMATE_ONLY_51FOLD_FROZEN_20261119.md` committed before opening source-model response.

## Source verified and executed

- One-shot [GitHub Actions #44544431206](https://github.com/zuizui0223/esdm/actions/runs/44544431206) completed successfully; synthetic source-only [Actions #44544309221](https://github.com/zuizui0223/esdm/actions/runs/44544309221) passed before it. Earlier [#44544012419](https://github.com/zuizui0223/esdm/actions/runs/44544012419) failed solely on an unused import from an unmerged secondary analysis module; that import was deleted before the synthetic gate passed. Preserve the earlier failure rather than calling it successful.
- Original GBIF 85,912 bat and 367,988 plant ZIPs were checked against the existing exact DOI-source SHA; original strict species×country 25km cell counts and source publication embargo reapplied.
- Plant model scores were **only** WorldClim BIO1/BIO12/coarse elevation-derived, fit using 106 original study botanical names and source-`datasetKey`-matched **GBIF recorded-cell vs other-plant pseudo-background**. No source-record intensity was inserted as a geographic plant predictor. Plant predictions are not true plant occupancy or available fruit biomass.
- Bat recorded-cell response: country withheld; training only outcountry focal observed cells vs other-bat recorded pseudo-background, 99 literature-link degree-preserving SN1 rewires per fit, same reg/scaling/samples for S0/S1/S3/SN1; NO original M0/M1/M3/N1 biological fit, true absence, independently measured effort, forest, actual fruiting or 3D behavior.

## Original full-fold accounting

| Stage | Count |
|---|---:|
| Original bat × country prefit fixed denominator | **84** |
| Previously 106-plant + source background training candidate folds | **51** |
| Actually fitted shadow bat-source ranks | **49** |
| Two source/raster quantity stops among 51 | **2** |
| Fitted species and country holdouts | **15 species, 10 countries** |

Two extra source/raster stops were **Artibeus jamaicensis × Belize** (6 strict bat test-positive cells, 4 test-background cells; requires >=5 of both) and **Artibeus lituratus × Belize** (4 test-positive cells, 6 backgrounds). All original 84 cases are present, including previously stopped 33.

## Mean rank AUC, across 49 modeled folds (unequal country composition)

| Shadow model | AUC |
|---|---:|
| S0: WorldClim BIO1/BIO12/elevation | **0.53118** |
| S1: S0 + generic 106 botanical source-score mean | **0.53472** |
| S3: S1 + *actual published* focal fruit-partner scores | **0.52903** |
| SN1: S1 + 99 degree-preserving rewired fruit-partner scores (mean) | **0.53703** |

- Mean **S3−S1 = −0.00569 AUC** (19/49, or 38.8%, positive).
- Mean **S3−mean(SN1) = −0.00800 AUC** (20/49, or 40.8%, positive).
- Across 10 countries with fits, equally weighted mean **S3−S1 = −0.01366** and mean **S3−mean(SN1) = −0.01496**; five countries' S3−S1 means positive, five negative.
- One nominal single-fold SN1 upper-tail `p<=0.05` among 49: **Artibeus lituratus × Costa Rica**, S3−S1 +0.09789, S3−SN1 mean +0.07385, one-sided rewiring upper-tail p=0.04 from 99 draws. This is **unadjusted over 49 source-dependent tests**, is not an independent confirmatory positive, and **does not** establish a true feeding mechanism.
- Prespecified full-cohort summary is negative, and no positive claim about partner identity transfer across regions is supported by this weak proxy model.

## Important sensitivity (exploratory, computed after opening the aggregate only)

El Salvador (SV) contributes two very small-n folds and a country mean **−0.125** S3−S1. If SV is **excluded post hoc solely as a diagnostic**, the 47-fold mean S3−S1 is **−0.00061** and 9-country equal mean **−0.00129**; SN1 mean contrast −0.00354. Therefore the sign/magnitude of the small negative overall mean is **sensitive to low-information country data**. Do **not** reinterpret this after-the-fact exclusion as a new primary result or claim true ecological absence of the fruit-link mechanism.

## Scientific outcome ceiling

This is an **exploratory null/non-support for incremental source-published fruit-partner predictor identity** conditional on coarse environmental signals and survey-biased botanical/bat background. It does NOT test food supply, realized bat foraging, source-independent plant suitability, actual distribution shift, causal tropic relationships, or the original complete M3−M1/N1 hypotheses. Coarse climate-only plant scores are nonlinear functions of the same abiotic inputs; model complexity and source observation biases persist. No forest, independently calibrated source effort, fruit/nectar biomass or seasonal feeding predictors were fitted.

**Keep original biological M3−M1 and M3−N1 as `null / not estimated`.** The result and every STOP remain immutable; no further tuning of the same opened source to chase positive findings. A new mechanism/replication claim needs truly independent botanical resource/detection or measured fruiting and independent bat response validation. Main branch unchanged.

Original output: `docs/replication/neobat/shadow_climate_only_51fold.json`, aggregate-only; no raw GBIF coordinates/IDs or per-cell predictions stored.
