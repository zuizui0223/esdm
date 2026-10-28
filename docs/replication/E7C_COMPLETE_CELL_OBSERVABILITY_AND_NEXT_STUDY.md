# E7-C sampling feasibility: large source archive does not imply complete species×time support

**2026-10-28 — strictly frozen-aggregate audit, post-outcome.** The [E7-C empirical source](E7_DIRECT_CAMERA_YEAR_FROZEN_RESULT_RECEIPT.json) is terminal. This audit reads only its prior **107,504-byte result JSON**, SHA256 `a032635e1acfabd89c253fe52308469735c4e13776ae3f49b7294cded9e7b6cf`, never the original 11 animal-record ZIPs or camera IDs. It does not refit E7, open a new ecological response, loosen support thresholds or reinterpret the original endpoint.

## Research question

What sampling structure is missing if we want to compare the wet-to-dry relative daily-record timing of two species **within the same physical camera and hydrological year**?

The original E7-C comparison required a strictly positive count in every cell of **2 species × 2 seasons × 2 clock windows = 8 cells**, then at least **10 complete camera-years**, **5 distinct physical cameras**, and **3 original collection-season folders** per pair/period. It reported 1/66 estimable pairs in discovery S01–S05 and 9/66 in validation S06–S11. The direct endpoint was selected *after* earlier E7 pooled outcomes were known, so none of this is independent ecological confirmation.

## Full support accounting, fixed 66-pair universe

| Matched complete camera-years per pair | Discovery S01–S05 | Validation S06–S11 |
|---|---:|---:|
| **0** | **30** | **27** |
| **1–4** | **23** | **20** |
| **5–9** | **12** | **10** |
| **≥10** | **1** | **9** |
| **Total** | **66** | **66** |

All 12 discovery and all 10 validation pairs in the 5–9 range already met both ancillary requirements (≥5 cameras and ≥3 original collection folders); **the shortage of complete camera-years was the decisive original gate** for those pairs. Within this range, **3 discovery pairs** and **1 validation pair** were exactly one complete camera-year below the fixed 10-year minimum. The median pair had only **one** fully observed shared camera-year in each split.

**Per-species complete-camera-year support is extremely uneven.** For example, zebra had **62 discovery / 118 validation** camera-years, wildebeest **32 / 59**, spotted hyena **4 / 13**, lion **6 / 5**, reedbuck **0 / 1**, warthog **1 / 0**. A species with no completely observed four-bin camera-year cannot qualify for *any* eight-cell pair comparison under this exact estimand. These are **missing recorded time-bin combinations**, not evidence that individuals or species were absent from the ecosystem.

## Prospective feasibility-only pairs closest to the 10-year support gate

The audit calculates, for every one of 66 pair IDs, the deficits in (a) complete matched camera-years, (b) distinct physical cameras and (c) source collection folders in both partitions. It reports a hypothetical lower bound on **additional fully observed camera-years for a separate future experiment** if each newly sampled camera-year can also add a new physical site and necessary collection period. The following pair names are selected **only by observable sample support, NOT by whether their ecological effect was positive**:

| Potentially feasible pair | Existing discovery complete camera-years | Existing validation complete camera-years | Theoretical minimum new complete camera-years across two separate future partitions |
|---|---:|---:|---:|
| Elephant / wildebeest | 9 | 13 | **1** |
| Giraffe / zebra | 9 | 17 | **1** |
| Grant's gazelle / zebra | 9 | 9 | **2** |
| Elephant / zebra | 7 | 13 | **3** |
| Giraffe / wildebeest | 7 | 10 | **3** |

**These are theoretical deficits, not realistic guaranteed survey costs, and absolutely not permission to add an invented or newly obtained original-season ZIP into the frozen E7-C endpoint.** Fully observed new camera-years cannot be conjured from already missing bins; species may not visit or be detectable in a time bin, source folders may not be extendable, and populations/cameras are correlated. A new environmental and observation protocol must be frozen separately before any genuinely new outcomes are opened. The original 1/66 vs 9/66 outcome remains unchanged.

## Why simply accumulating images may not solve the problem

A transparent **illustrative** observation model assumes eight **independent Poisson counts** with the same expected number `lambda` of *recorded sequences* per species×season×time bin. The probability all eight counts are nonzero is

`P(complete pair-year) = (1 - exp(-lambda))^8`.

| Hypothetical recorded-sequence expectation per cell | Probability eight cells are positive |
|---|---:|
| 1 | 2.55% |
| 2 | 31.25% |
| 3 | 66.46% |
| 4 | 86.25% |

Under **this illustration alone**, reaching 80% pair-year completeness would require about **3.59 expected records in *each* of the eight cells**; 90% requires **4.34** each. If a single cell has mean 0.2, even if the other seven cells have extremely many records, overall completeness is **at most 18.1%**. Real camera sequences are autocorrelated, heterogeneous, and conditional on effort and triggering; Poisson independence and common `lambda` are **not assumptions we have verified for Serengeti**. These numbers are sampling intuition, **not fitted biological predictions or statistical confidence intervals**.

## Concrete next *independent* ecological evidence design

1. **Expose denominators:** at each physical camera × day/night × wet/dry × year unit, log operational exposure and camera downtime, not only identified sequences. If a time bin has zero records but unknown exposure, it cannot distinguish non-operation from a truly unrecorded species.
2. **Independently calibrate visibility and detection:** pair camera traps with synchronized known-passage/reference-video intervals, retained at the site×taxon×clock-bin level. Make sensor positions/vegetation/effort metadata comparable and preserve independent physical-camera cluster IDs.
3. **Select a tractable multispecies panel before opening independent outcomes:** stratify camera placement to cover both nocturnal/diurnal activity windows and both seasons; use the current support-only deficits as planning context, **not effect-direction screening**. Do not demand 12 taxa share every camera-year unless the predicted observation process justifies it.
4. **Prespecify environment and transfer:** select measured site-level rainfall/NDVI/vegetation and habitat covariates *before* inspecting new diel outcomes, plus genuinely unused locations/years with source protocol crossing. Analyze the recorded time-bin counts including zeros using effort offsets and a detection component only where reference observations identify it.
5. **Publish the full support/selection ledger:** all originally targeted pairs, empty recorded bins, operational exposure, original/validation camera clusters and any technical stop. Keep original E7-C as its frozen terminal endpoint and never use retrospective lowering of the ten-year, five-camera or three-collection gate to rescue it.

## Scientific interpretation

This result is a **positive design-level finding**: the relevant ecological sample size is *complete camera-year cross-season/night-day co-observation*, not the raw archive's approximately 2.66 million image-associated sequences. Most old E7 pair effects cannot be tested with a strict non-pooled same-cell comparison because of that actual overlap limit. The cause of any particular missing bin — true absence, seasonal movement, temporal specialization, camera inactivity, image registration, or sensor detection — **cannot be identified from aggregate support counts alone**.

This closes the E7-C exploratory audit rather than starting another semisynthetic model generation. It leaves the original E4 score, E5 0/17/G4, E7 11-season results and E7-C 1/66 vs 9/66 unchanged.

**Reproducibility:** run [the frozen-aggregate script](../../scripts/e7c_future_observability_audit.py) on the exact archived [E7-C original result artifact](https://github.com/zuizui0223/esdm/actions/runs/40618416135/artifacts/12785339858). No biological response file or camera-name export is needed.
