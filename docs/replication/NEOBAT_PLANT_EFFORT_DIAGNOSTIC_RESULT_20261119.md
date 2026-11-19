# NeoBat original plant country-crossfit source-effort diagnostic — confirmed computational result, not ecological validation

Date: 2026-11-19. The original response was already opened in the previous 3-plant Colombia pilot, so this is **post-hoc exploratory**. The first diagnostic run [#44534280720](https://github.com/zuizui0223/esdm/actions/runs/44534280720) failed **only at JSON serialization** of a NumPy int64 pair count and remains failed. The corrected distinct run [#44534817932](https://github.com/zuizui0223/esdm/actions/runs/44534817932) passed after the type-only correction and source-free regression (including an original-shaped NumPy JSON test).

Original GBIF plant DOI ZIP, WorldClim BIO1/BIO12 and elevation SHA pins all matched; exactly the same three sentinel plants, Colombia withheld, source-cell counts, and original abiotic / combined AUCs were reproduced **exactly**. No bat model or additional plant selection.

## Empirical rank AUC diagnostic

| Frozen taxon | Abiotic-only AUC | Other-plant recording-intensity proxy only | Abiotic + recording-intensity proxy | Increment beyond proxy | Exact proxy-intensity conditional AUC | Exact comparable-pair coverage |
|---|---:|---:|---:|---:|---:|---:|
| *Cecropia obtusifolia* | 0.526 | 0.730 | 0.736 | +0.006 | 0.609 | 5.76% |
| *Ficus insipida* | 0.499 | 0.797 | 0.783 | −0.014 | 0.534 | 4.57% |
| *Piper aduncum* | 0.505 | 0.849 | 0.847 | −0.002 | 0.606 | 2.89% |

Exact proxy-intensity AUCs include only focal positive × target-background pairs where **the exact number of recorded other plant taxa is equal**. They do not characterize all species×cell comparisons. Coarser fixed bins `[1],[2-3],[4-7],[>=8]` yielded AUCs for the combined model 0.600 / 0.629 / 0.678, with only 24.9% / 22.4% / 22.3% comparable pair coverage. Conditional estimates do not establish causal ecology or independent detection calibration.

## Scientific finding and implementation consequence

**The apparent AUC 0.736–0.847 from the preceding plant pilot is nearly entirely reconstructable using the source-derived count of other plant taxa observed at the same 25km cell.** The extra annual-mean temperature, precipitation and coarse elevation predictors provide **−0.014 to +0.006** AUC beyond that covariate for these three Colombia sentinels. This rejects neither environmental niche structure in nature nor the fruit-partner hypothesis, but **the current 3-species source-derived plant model does not support interpreting high rank AUC as measured ecological plant availability or fruit biomass**.

The observation-derived proxy may include actual plant richness, localized biological habitat and collection effort; it is **not** independently observed survey effort. Because the original source is already opened and these tests are post-hoc, this is a *data/measurement failure-mode result*, not confirmatory ecological evidence. Do not scale the same proxy method to 106×17 and report resultant plant suitability or M3 ecological performance as a primary result.

## Next source-identification task

Test whether target-group botanical background can be constructed **within the same original GBIF `datasetKey`** as the focal plant in each heldout country. Enumerate source-dataset–conditioned positive/background cells, preserving 106 candidate species and 17 holdout countries; report all failures, no inference that `datasetKey` implies an effort-matched field survey. If not enough matched source support, stop this data track instead of changing AUC thresholds or retrospectively choosing promising species. Independent mapped plant resource abundance/fruit phenology would still be required to infer actual feeding resources.

Original 255-plant v1 remains frozen and unestimated. Exploratory v2 has 79 bat-fold source background input candidates, **not 79 completed ecological comparisons**.
