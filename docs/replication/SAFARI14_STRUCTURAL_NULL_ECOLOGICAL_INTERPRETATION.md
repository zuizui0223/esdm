# S14 post-result validity check: observed turnover dominance is not evidence of nonrandom assembly by itself

**Completed 2026-11-14; explicitly retrospective**. The original observation [Safari14 12-eligible-park source and results](SAFARI14_SPATIAL_BETA_FROZEN_RESULT_RECEIPT.json) remain fixed, including the pre-specified two-partition result that Simpson turnover exceeded nestedness-resultant dissimilarity in **500/500 original camera subsamples**. This check reads ONLY the originally archived **39,552-byte aggregate result JSON**, not animal sequences or the original camera-by-species matrix.

## What new mathematical question was tested?

Would the same headline *turnover > nestedness* appear if parks had **no distinct ecological species selection mechanism** and simply received independent random sets from a common 38-label pool, with each park's recorded **median rarefied label count** preserved?

The original positive partition-median result alone does not answer this. As soon as two equally rich artificial species sets contain different species, the Simpson turnover component is often substantial while nestedness-related dissimilarity is near zero. Such an outcome could be an expected combinatorial property rather than evidence of ecological replacement above random expectation.

The **post-outcome illustrative** scenario fixes all 12 original eligible park codes (7 discovery / 5 validation), 500 artificial independent park-set draws each, exactly 38 globally recognized original labels, original per-park median 10-camera richness rounded to the nearest integer half-up, and the same pairwise Baselga `β_sor = β_sim + β_sne` calculations. Weights for drawing label `i` without replacement are `w_i = (total source image annotation rows for label i)^α`, for **α = 0, 0.5, 1**. All are reported; α is **not estimated from observed park membership**.

The source image-label frequencies are *not* unbiased species occurrence rates or passage counts. In particular, α=1 is a deliberately strong counterfactual weighting that may overrepresent animal species appearing in many images or bursts. These are **structural demonstrations, not formal ecological null models or statistical significance tests**.

## Successful source-backed aggregate analysis

[GitHub Actions run 43577782379](https://github.com/zuizui0223/esdm/actions/runs/43577782379) succeeded with **5 synthetic tests passed**; input original-Safari14 inner JSON SHA256 `f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7` verified. Output [artifact 14106593727](https://github.com/zuizui0223/esdm/actions/runs/43577782379/artifacts/14106593727), ZIP digest `sha256:a8e71dc30fdb2f0e102bc5d1b75dc4305e07cf975be854205598d53dd2e4b0be`, inner JSON SHA256 `c4cacd72617d414791e2f44cc8832fad982b00e4f4187d103bdc8ee3f727b303` (6,226 bytes). **No new wildlife event/image/camera record was read or downloaded.**

### Artificial assignment compared with actual observed partition medians

| Scenario: source image-label sampling weight | Discovery β_sim | Discovery β_sne | Discovery turnover-dominant null draws | Validation β_sim | Validation β_sne | Validation turnover-dominant null draws |
|---|---:|---:|---:|---:|---:|---:|
| **Original observed, fixed 10-camera draws** | 0.444 | 0.126 | **500/500** | 0.356 | 0.063 | **500/500** |
| **Uniform 38 labels, α = 0** | 0.588 | 0.084 | **500/500** | 0.540 | 0.030 | **500/500** |
| **Moderate label-frequency weighting, α = 0.5** | 0.333 | 0.167 | **485/500** | 0.321 | 0.049 | **500/500** |
| **Strong label-frequency weighting, α = 1** | 0.111 | 0.222 | **4/500** | 0.144 | 0.063 | **494/500** |

Original observed medians use 500 resamplings of *real camera station subsets*; artificial medians use 500 completely different *draws of species sets*. They are **not two samples from an equivalent experimental distribution**. Do not interpret differences between these numbers as Monte Carlo P values, confidence intervals, ecological standardized effect sizes, or test evidence of positive filtering.

**Decisive falsification:** Uniform random assignments had turnover dominance in **500/500 null draws in both splits**. Therefore 500/500 dominance as a stand-alone criterion cannot distinguish actual park-specific species assembly from purely combinatorial randomized membership. The original observational result remains accurate, but its biological interpretation must be **downgraded to descriptive recorded-community differentiation**, unless a more realistic null/model is independently specified and tested.

**Why the α sensitivity differs between partitions:** The observed median 10-camera species counts span **6–19.5** in the discovery parks versus **13–20** in validation; the median absolute richness difference between park pairs is **6 vs 2 labels**, respectively. A strongly common-label-weighted species pool therefore tends to produce more *nestedness* in the highly uneven discovery assemblages than in the more uniformly rich validation assemblages. This is an explanatory mathematical feature of the artificial scenario, not proof that differences in real reserves were caused by this process.

## What this does and does not establish

**Supported now:** detected mammal species sets differ among parks, and observed pairwise dissimilarity components were turnover-dominant under equal-camera sampling. The *diagnostic strength* of that fact is weak when compared against plausible but simplistic random-species-set constructions. Simple turnover dominance cannot by itself support a claim about non-random community assembly, landscape barriers, environmental filtering, conservation complementarity **above random baseline**, phylogenetic differentiation, or regional species loss.

**Still unmeasured:** park-by-species incidence *marginals*, real camera active-day exposure and detector sensitivity, spatial/environmental distances between parks, independent reserve survey programmes, and a biologically defensible regional available-species pool. An appropriate future null should preserve the actual camera-level or park-level species incidences, the richness/occupancy constraints relevant to the scientific question, known camera effort and the fixed project/validation separation. It should be prespecified before opening fresh environmental-response data; no new threshold tuning or retrospective E4/E5/E7 rescue is authorized.

This is a **positive validation of the scientific caution**, not a new animal field-data effect: apparent support for an assembly claim may arise under a very simple null.

## Immutable lineage

- [Original frozen Safari14 observational result](SAFARI14_SPATIAL_BETA_ECOLOGICAL_SYNTHESIS.md) and source SHA.
- [Retrospective diagnostic definitions and limitations](SAFARI14_STRUCTURAL_NULL_DIAGNOSTIC.md).
- [Full simulated sensitivity artifact](https://github.com/zuizui0223/esdm/actions/runs/43577782379/artifacts/14106593727) and [machine-readable result receipt](SAFARI14_STRUCTURAL_NULL_RESULT_RECEIPT.json).
- Original E4 predictive outcomes unchanged; E5 remains **0/17 standard-qualified, G4 unpassed**; E7 seasonal relative diel transfer and E7-C exact-support results unchanged. This script performs no eSDM field fit and no new biological source opening.


## Distinct later fixed-incidence test (also 2026-11-14)

The earlier **richness-median-only random-set null** remains a valid
falsification of the claim that β_sim > β_sne *alone* diagnoses nonrandom
assembly. A [separate S14-FM analysis](SAFARI14_FIXED_MARGINS_NULL_ECOLOGICAL_RESULT.md),
with a protocol frozen before its camera-level response opening,
reconstructed the original eligible camera×mammal incidence and
conditioned on **both** each camera's species richness and each species'
number of recorded cameras *within each park partition*. It found
observed median β_sim **larger than the incidence-margins null in
500/500 paired camera subsamples** in the original 7 discovery and
5 validation parks. This later result provides positive evidence for
**recorded park-specific species sorting relative to that more
restrictive conditional-null model**, but neither analysis identifies
ecological environmental filtering, true absence/occupancy, measured
camera detection or independent reserve-provider replication.

The original weak-null result was **not overwritten**, and the two null
families answer different mathematical questions. Neither should be
reported as a formal P-value or an experimentally identified mechanism.
