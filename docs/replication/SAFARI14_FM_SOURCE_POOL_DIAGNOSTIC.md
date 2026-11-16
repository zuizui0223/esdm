# Safari14 S14-FM: park influence and public landscape-description contrasts

**2026-11-16. Post-outcome, read-only diagnostic. Not a new wildlife source opening, pre-registered test, independent validation, or eSDM fit.**

## Frozen inputs and mechanical checks

The starting ecological evidence is [S14-FM PR #232](https://github.com/zuizui0223/esdm/pull/232): the observed reserve replacement pattern exceeded the camera-richness + species-positive-camera fixed-margins randomization in both original partitions, with 500/500 positive *paired subsampling/randomization comparisons* each. The 500 are **not** 500 independent parks and the study establishes no formal ecological p-value.

This diagnostic reads only the original [S14-FM Actions artifact 14107094556](https://github.com/zuizui0223/esdm/actions/runs/43580142370/artifacts/14107094556), enforcing ZIP SHA256 `a9f32536b4120c249abd57c59981e6cfcaab4deb19016b788a0000ac35bd06dc` and inner JSON SHA256 `4dcf8212510524dccefbfa250e05277fe55085f3b838c33a1c5f7fc8ee593b5e`. Each of the 31 original *within-partition* park-pair records must occur exactly once, have 500 estimable null draws, and satisfy `pair_median_excess = median(observed β_sim per draw) − median(null β_sim per draw)` to numerical precision. No source images, camera incidence matrix, raw observations or time series are accessed, and the old outcomes are never modified.

**Distinct descriptive estimand:** median **across park pairs of their archived pair-level median excesses**. This **is not** the original S14-FM primary value, which was a *median across 500 paired draws of each draw's park-pair median difference*. Neither reaggregation is a confidence interval or a significance test.

## No single park dominates the *pair-summary* statistic

| Frozen split | Eligible parks | Park pairs | Positive pair-level contrasts | All-pair median of pair-level excess | Range after deleting each park | Positive leave-one-park summaries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Discovery | 7 | 21 | 19/21 | +0.400 | **+0.333 to +0.438** (15 pairs per deletion) | **7/7** |
| Validation | 5 | 10 | 10/10 | +0.242 | **+0.211 to +0.301** (6 pairs per deletion) | **5/5** |

No single reserve determines the **direction of this particular pair-summary aggregate**. But the directional leave-one-out outcome is largely guaranteed by the already-known 19/21 and 10/10 positive pair counts. It is primarily an influence/concentration description, **not additional independent empirical confirmation**. All remaining pairs after dropping one park are still dependent and no spatial block confidence interval is available.

## A more informative exploratory source-pool pattern

The public [LILA Snapshot Safari 2024 Expansion project descriptions](https://lila.science/datasets/snapshot-safari-2024-expansion/) independently state the following landscape relationships among the seven discovery reserves. Crucially, **the pair selection was made only after the S14-FM results were already known**; these are explanatory examples, *not* a prospective matched-pair test or a GIS-derived biome map.

| Publicly documented relationship | Original observed β_sim pair median | Fixed-margins null median | Observed−null | Small-excess rank among 21 |
| --- | ---: | ---: | ---: | ---: |
| **APN–KRU**: adjacent, unfenced APNR/Kruger aligned grid | 0.071 | 0.100 | **−0.029** | 2nd |
| **CDB–KAR**: both explicitly in the Nama Karoo biome | 0.125 | 0.167 | **−0.042** | 1st |
| **KGA–LEC**: both in the Kalahari region | 0.429 | 0.250 | **+0.179** | 5th |

The median excess across these **three retrospectively selected, non-overlapping pairs** is **−0.029**, compared with **+0.436** across the other 18 discovery pairs (difference **−0.464**). The two *only* negative-excess discovery pairs, APN–KRU and CDB–KAR, correspond to the public connected-grid and shared-Nama-Karoo cases. KGA–LEC is not negative, but its positive excess is among the five smallest.

**Ecological reading (hypothesis, not mechanism identified):** a null that shuffles species labels among all cameras within a broad multi-reserve partition may overstate an ecologically implausible expectation across distinct regional pools; more comparable or connected reserves may share species and therefore exhibit smaller observed-minus-null replacement. This pattern is compatible with landscape connectivity / biome/source-pool structure. It is **also** compatible with protocol, taxon visibility, effort and unmeasured detection differences, and the public park descriptions are too coarse to quantify similarity or accessibility. The three pair links have different strengths (direct unfenced contiguity vs broad named biome) and cannot be treated as equivalent environmental-distance measurements.

Do not infer a p-value from their ranks, treat country labels as biome, or promote this post-outcome alignment to positive proof of dispersal limitation or habitat filtering. The 5 validation parks do not provide a pre-registered replicate of the same three contrasts. This research question now needs *independently measured camera operating effort/detection and geographic habitat/source-pool matrices* plus an **unopened independent reserve network and fixed analysis design**, not another tuning cycle on Safari14.

## Reproduction and status boundaries

```bash
python -m pytest -q tests/test_safari14_fm_source_pool_contrast.py
python -m scripts.safari14_fm_source_pool_contrast \
  --source-zip path/to/s14_fixed_margins_null.zip \
  --output docs/replication/SAFARI14_FM_SOURCE_POOL_DIAGNOSTIC_RESULT.json
```

The resulting deterministic [aggregate-only JSON](SAFARI14_FM_SOURCE_POOL_DIAGNOSTIC_RESULT.json) has SHA256 `9ab06b209ef56fa9a776d9fbf6ee0bdd012a2df6fc13ef1bc8e2442fc3100e31`. The local synthetic test suite passed **8/8** tests. This is a reproducible diagnostic of the *already-frozen* source summaries. **Original E4 negative activity predictive gain, E5 0/17 qualified data, E7 transfer failure, E7-C support limitation and S14-FM descriptive conclusion are unchanged.**
