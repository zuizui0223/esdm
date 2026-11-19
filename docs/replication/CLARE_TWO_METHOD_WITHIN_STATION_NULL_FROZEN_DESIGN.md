# Clare 2017: pre-response frozen station-conditioned camera×snow-track detection association

**2026-11-19; frozen before opening any of the original camera/snow detection values.** This is a distinct single-region (Maine, USA) empirical observation-process analysis, not an E5 qualified candidate and **not** a new SDM process-model generation.

Public source: Clare, McKinney, DePue & Loftin (2017) [Dryad dataset DOI 10.5061/dryad.4mt00](https://doi.org/10.5061/dryad.4mt00), version **1** (verified from its public dataset REST API during B1), companion paper DOI [10.1002/eap.1587](https://doi.org/10.1002/eap.1587). The public release has six small files. The frozen outcome source is **only** `MartenOccupancyEncounters.csv`: 238 stations × up to 9 repeated survey occasions, with response codes **1=camera only, 2=snow tracks only, 3=both, 4=neither**, missing for inactive occasions, exactly as described by its DOI's usage notes. Do not inspect or select sex, individual marten, fisher covariates, camera images or station coordinates for this original test.

## Prespecified source retrieval

Use the canonical public Dryad v2 REST endpoint `https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.4mt00` to confirm `identifier` contains exactly `10.5061/dryad.4mt00` and `versionNumber=1` BEFORE any source acquisition, then download the original exact version through `https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.4mt00/download` exactly once. If transport yields HTML, an inaccessible/non-ZIP payload, an unexpected/missing `MartenOccupancyEncounters.csv`, source version change or ambiguous duplicate filename, return `TRANSPORT_OR_SOURCE_STOP` without alternate mirrors or reruns. Record original ZIP SHA256 and target file SHA256. No raw event rows or station IDs will be committed to GitHub artifacts.

## Frozen response parsing and support

Require exactly **238** source station rows and exactly **9** coded occasion columns; an optional first station-ID column may be present if all its values are unique and nonempty. A single initial nonnumeric header line is allowed when its width equals the subsequent rows. No adjustment of the station count, date windows or response codes after access. Treat strings `NA`, `NaN`, blank as unobserved; accept only observed integer codes 1,2,3,4. Stop on any other code, inconsistent column count or duplicate station identity. Do not silently turn NA into absence.

For each observed station×occasion define `C=1` for codes {1,3}, `T=1` for codes {2,3}. The number of observed paired occasions is `m_i`, camera positive count `c_i`, track positive count `t_i`, and both positive count `b_i`. Under the **within-station temporal permutation null** (camera occasions fixed, track detections exchangeable across observed occasions within each station, holding marginal station counts fixed), the exact expected joint detections are `sum_i c_i*t_i/m_i`. Primary descriptive effect:

```
Delta = (sum_i b_i - sum_i c_i*t_i/m_i) / (sum_i m_i)
```

This **controls site-averaged camera/track counts** but not within-site snowfall, weather, baiting or animal-activity time variation, and it does not condition on true occupancy. Estimate a **station-cluster descriptive 95% bootstrap interval** for Delta by 2000 resamples of the 238 stations with replacement, fixed Python seed **20261119**, equal station weight per resampling unit then ratio by resampled total observed occasions. No p-value; station spatial dependence is not calibrated and this bootstrap is not a formal geographical uncertainty interval.

Support gate: at least 150 stations with 2+ observed paired occasions, ≥500 total paired occasions, ≥25 camera-detection occasions and ≥25 snow-track detection occasions; any failure gives `INSUFFICIENT_SUPPORT`. Output raw 2×2 aggregate counts (camera only, track only, both, neither), total observed, unobserved cells, statistic, cluster-bootstrap interval, observed and null co-detection **without raw station IDs**. Primary directional rule: `POSITIVE_WITHIN_STATION_ASSOCIATION` iff Delta ≥+0.020 and bootstrap lower bound >0; `NEGATIVE_WITHIN_STATION_ASSOCIATION` iff Delta ≤−0.020 and bootstrap upper bound <0; otherwise `INCONCLUSIVE_SIGNED_EFFECT`. Do not tune this margin, seed, station grouping or intervals after response opening.

## Claim limits

Even a positive result demonstrates only **co-occurrence of detections by the two methods within stationary monitored occasions beyond an exchangeable permutation reference**. It cannot alone identify observer covariance *conditional on true animal presence*, because within-site animal traffic, snowfall and other time-varying exposures could drive both methods. Snow tracks may yield species-classification false positives; they are not an independently counted denominator of all marten passages through the camera field of view. No eSDM superior prediction, causal mechanism, multi-region transfer, true occupancy, abundance or E5 G4 pass can follow from this calculation. Original E5 stays **0/17** and frozen E4/C1–C3/D1/Safari14 results are untouched. This is a transparent bounded secondary observation-process application, not a reproduction of all Clare et al.'s multi-method occupancy/false-positive models.

One authorized GitHub Actions run on the new PR's opened event; archive outcome or honest stop, retire the workflow, do not replay the consumed source with changed parsing or cutoffs.
