# E4–E5: quantitative diel-attribution frontier (no new biological fit)

**Date:** 2026-10-13. **Status:** post-result algebraic sensitivity analysis using **previously frozen E4 aggregate counts/rates only**. This is neither a new E4 endpoint nor a qualified E5 empirical detection analysis. No raw event records were opened, no likelihood or posterior was recomputed, no candidate was rescored, and no existing conclusion was reclassified.

## Question and fixed comparison

How different would **true local animal passage** and **effective camera observation** have to be to explain the weaker recorded night/day contrast in the frozen east transfer? The two non-equivalent observed cohorts in the existing post-result record are:

| Existing cohort | Frozen recorded night/day event-rate ratio |
| --- | ---: |
| Training `StateAnnotatedCount` | `13.4047664930` |
| Heldout D-prefixed source stratum | `2.9645385457` |

The **ratio of these two ratios** is `C = 0.2211555529` (reciprocal `4.5217042`, log `-1.5088890`). Thus the recorded night/day contrast in heldout D was approximately 22.1% of the annotated-training contrast, or **4.52-fold weaker**. Both groups still had more recorded events per camera-day at night than by day. The comparison is descriptive and **not a matched causal contrast**: geography, camera/source stratum, composition of sites and sampled calendar times differ. D was absent from the annotated-training stratum.

## Exact accounting identity, not identified mechanisms

For regime `r`, diel bin `t` and known reference-zone passes, define recorded event rate per unit effort as

`Y[r,t] / E[r,t] = A[r,t] * D[r,t]`.

`A` denotes the **effort-weighted intensity of actual animal passage within the reference zone**, *not* regional population density; `D` denotes the **passage-weighted probability of producing the observation endpoint**, including passage composition, trigger, registration and annotation. At an aggregated regime/bin level, the identity remains exact when `D` is weighted by the actual passes contributing to `A`; it is not generally a product of unweighted averages over cameras.

Let `R_obs,r`, `R_pass,r`, `R_det,r` be the night/day ratios of the respective quantities, and let `P = R_pass,heldout / R_pass,training` and `Q = R_det,heldout / R_det,training`. Then

`C = R_obs,heldout / R_obs,training = P * Q`.

For the actual frozen recorded ratios, `P * Q = 0.2211555529`. **This is one equation with two unknown cross-regime ratios**. The data do not identify a specific `P` or `Q`, and other shifts in site and seasonal composition prevent an unqualified ecological interpretation of either factor.

| Hypothetical change in detection diel contrast, `Q` | Required passage diel contrast change, `P = C/Q` |
| ---: | ---: |
| `0.20` | `1.10578` |
| `0.25` | `0.88462` |
| `0.50` | `0.44231` |
| `1.00` | `0.22116` |
| `2.00` | `0.11058` |

These are **counterfactual factor pairs**, not fitted detection factors, estimated effect sizes, priors, uncertainty intervals, or likelihoods. In particular:

- If actual passage diel contrast were identical between cohorts (`P=1`), the **relative night/day effective detection contrast** would have to be `Q=0.22116`, i.e. a roughly 4.52-fold drop. This is not the claim that each camera's total sensitivity declined by 4.52-fold.
- If effective detection's night/day contrast were identical between cohorts (`Q=1`), passage diel contrast would have to drop by a factor of about 4.52. This is not evidence that muskrats changed their intrinsic diel behavior by that amount.
- `Q<0.22116` permits `P>1`: a **more nocturnal true passage contrast in heldout D** could coexist with a weaker *recorded* contrast. This is a mathematical possibility, **not an observed ecological inversion**. Distinguish this cross-regime direction reversal from within-regime night/day inversion.

No arbitrary bound on `Q` is imposed because **none was independently measured in the E4 MICA camera network**. Do not transfer the separate Findlay fox near/far stage estimates into MICA to manufacture such a bound.

## Empirical design that would resolve the missing term

To distinguish these explanations, the next independent study must collect **both missed and recorded reference-zone passages** under continuous CCTV or an equivalently audited passage denominator, together with per-passage day/night timing, distance, speed/trajectory, camera configuration, stage-specific trigger/registration outcomes, and stable physical-deployment identities. It must **cross geography with sensor/protocol** and track exposure/season so an apparent regional contrast is not a source-only contrast. The original frozen E5 minimum of 20/10 physical sites and six distinct calendar months in each geographic split still applies to any claim of original E5 qualification; nothing here modifies that contract.

The independently published Findlay et al. (2020) methods explain that CCTV passages were logged chronologically and camera events cross-referenced by timestamps ([DOI](https://doi.org/10.1007/s13364-020-00478-y)). However, the two currently released FOX/BADGER stage CSVs have no independently verified persistent shared passage ID: 881/881 source-row positions agree, but 351 rows have nonunique covariate fingerprints. Author-supplied original timestamp/pass keys would strengthen that **separate donor's** provenance; they would still not supply geographic transfer for E4 or pass original E5 G4.

## Reproduction and decision boundary

Run `python scripts/e4_e5_diel_attribution_frontier.py` to print the exact factorizations. This reads only `E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json`, checks the existing E4 outcome provenance and preservation flags, and uses only two **previously reported summary ratios**. Tests check the multiplicative identity, positive-domain validation, and frozen-source contract.

**Allowable statement:** the observed 4.52-fold difference is compatible with infinitely many ecological passage and observation-process changes; independent known-pass calibration is needed before attributing it to behavior. **Not allowable:** a positive detection-effect finding, an observed reversal in true activity, a predictive improvement, an E4 refit, validation of Findlay stage ID linkage, or E5 G4/candidate qualification. These limitations also apply to the scenario table.

Related unchanged evidence: [`E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json`](E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json), [`E4_E5_ECOLOGICAL_EVIDENCE_SYNTHESIS.md`](E4_E5_ECOLOGICAL_EVIDENCE_SYNTHESIS.md), [`E5_INDEPENDENT_ACTIVITY_DETECTION_QUALIFICATION_CONTRACT.json`](E5_INDEPENDENT_ACTIVITY_DETECTION_QUALIFICATION_CONTRACT.json).
