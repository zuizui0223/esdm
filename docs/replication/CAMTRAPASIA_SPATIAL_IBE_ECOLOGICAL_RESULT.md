# Independent C1 CamTrapAsia mammal assemblage distance-vs-environment result

**C1 completed 2026-11-17 JST, one source-backed response opening.** A prior launch of this same PR failed at a pre-response shell line-break syntax error: [run 43894380721](https://github.com/zuizui0223/esdm/actions/runs/43894380721), source acquisition skipped, no capture response opened. The workflow was corrected before response, and a technical PR close/reopen generated one actual source-backed run [43894683151](https://github.com/zuizui0223/esdm/actions/runs/43894683151), whose synthetic pre-response tests and one empirical source check succeeded. This did **not** change the original [design fixed before capture-response opening](CAMTRAPASIA_SPATIAL_IBE_FROZEN_DESIGN.md), already committed at `242837f500588dda609d57f570b7d888aa7a41bd`.

## Source provenance and independent character

- Mendes et al. (2024), *CamTrapAsia: A dataset of tropical forest vertebrate communities from 239 camera trapping studies*, *Ecology* 105:e4299, [Zenodo 10780971](https://doi.org/10.5281/zenodo.10780971). This source pools tropical Asian survey authors and is geographically and ecologically distinct from African Snapshot Safari. It is **not** an independent sensor-calibration denominator.
- Original file MD5 in Zenodo matched for metadata, captures, and traits: `2b50c534737b0c98a93da54128b10a32`, `a73975d7626def4012a4e1197497ba87`, `59e0748f8aaf59b23b936248f1e63fc9` respectively. Exact SHA256 hashes for all three are in the [unmodified frozen result JSON](CAMTRAPASIA_SPATIAL_IBE_FROZEN_RESULT.json).
- Successful one-shot result [Actions artifact 14238886654](https://github.com/zuizui0223/esdm/actions/runs/43894683151/artifacts/14238886654), ZIP SHA256 `68e1d4f174f982be2d8739912361dd4a2d7f2fe31c6d7bf53433e304a5e20dd4`, inner JSON SHA256 `64d02cf51e52d53046baa64d7ffb9cb624037a9d16a35e9e732fda2abece0dc1` (3,805 bytes). The frozen source JSON is committed **unchanged** under the filename above; biological event records and raw survey-level species/camera IDs are not exported in the artifact.

## Exact sample support and descriptive community structure

The dataset has **239** reported study-metadata rows. The frozen independent-exposure rule retained **193** studies with at least 500 camera-trap nights and 10 cameras (46 excluded). The mammalian taxonomic and >=2 independent-record threshold, then >=5 mammal-species rule, retained **154** analyzable study assemblages. These were assigned entirely by `(country, landscape)` to **121 discovery studies in 51 landscapes** and **33 heldout studies in 14 landscapes**. All support gates passed. This is a new *study-level* response—not 154 independent populations and not a camera-by-species fixed-degree null.

| Frozen partition | Study pairs | Median pair Simpson β_sim | Pairs with positive β_sim | Median pair distance |
|---|---:|---:|---:|---:|
| Discovery | **7,260** | **0.500** | **98.77%** | **1,305.5 km** |
| Validation | **528** | **0.553** | **99.81%** | **1,674.3 km** |

The near-universality of recorded mammal replacement across *Asian study assemblages* is a geographical-scale descriptive observation: it is not the Safari14 question of an excess over a camera-marginal null and cannot directly prove that landscape dispersal constraints or environment caused it.

## Frozen out-of-landscape prediction: environment did not add validated benefit

The prospectively specified question was whether a four-covariate 20-km **environmental distance** (forest cover, precipitation, temperature and human footprint) adds out-of-landscape predictive information beyond log geographic distance and recorded trap-night ratio. Both models used exactly ridge penalty α=5, fixed study/landscape eligibility and the same holdout pairs. Median differences were not optimized after source opening.

| Fit / evaluation | Geography + effort baseline (G) | G + environmental distance (G+E) |
|---|---:|---:|
| Discovery standardized geographic coefficient | +0.12360 | +0.11571 |
| Discovery standardized environmental coefficient | — | **+0.01990** |
| Heldout mean absolute error (MAE) | **0.133083** | **0.136163** |

**Primary heldout MAE gain (baseline MAE minus full MAE) = −0.003080.** This fails the exact frozen requirement **gain ≥ +0.020 AND positive environment coefficient**. Status: `C1_EVALUATED_NO_INCREMENTAL_PREDICTIVE_EVIDENCE`. The positive environmental coefficient on discovery alone would have been misleading if promoted to an ecological success.

Both predeclared directional subgroups remained negative: within-country pairs (107 pairs) **−0.001613** MAE gain, different-country pairs (421) **−0.003453**. These are dependent pairs, not inferential replications. Named original study sources are not fully blocked: **7 source strings** occur in both discovery and validation (55/20 distinct source names in the respective partitions), despite geographic landscape-group blocking.

## Ecological interpretation and limits

**Supported:** Across heterogeneous tropical Asian camera studies, recorded mammalian community composition generally differs between study regions. At this observation grain, positive geographic distance association appears in a fitted training relationship, while this particular 20-km four-variable environmental distance **did not improve independent-landscape prediction** after geographic distance and recorded effort ratio were considered. This is a bounded predictive negative result, not proof that IBE is absent from ecology, that climate is unimportant, or that geography itself is causal.

**Unidentified:** species availability/source pools, river/ocean barriers, true mammal occupancy and dispersal, hunting pressure versus its proxies, species-specific camera-detection probability, site-level abundance, or direct animal community interactions. The studies span different years, camera protocols and original observers. The 7 source strings shared across partitions can introduce correlated study/reporting processes. Our fixed observation rule retained reported mammal taxa even if categorized as domestic in the source; it does not isolate strictly wild-fauna responses. Raw species IDs remain within publicly available input; no newly inferred individual animal locations are claimed.

**Comparing projects:** This negative result does not negate Safari14's observational fixed-degree randomization excess (an entirely different estimand). It also does not validate/falsify the frozen v0.4-R5b process-based eSDM, FIELD1, MAP1, E4, E5, E7 or E7-C. In particular, no activity/detection process was separately identified, no model comparison of the actual eSDM against a conventional SDM took place, and E5 remains **0/17** qualified. Do not re-run C1 on the same source with altered effort cutoffs, selected fauna or extra environmental variables to rescue the negative prediction.

## Status decision

**Freeze C1 as a successful one-shot independent biological opening with a negative incremental-environment result.** Further support requires a new independently designed source-pool/detection-controlled study or a new question, not source reopening and threshold tuning. All source hashes, code, and results are inspectable; the C1 biological data themselves are not mirrored into this repository.
