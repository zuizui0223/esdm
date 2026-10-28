# E7 post-result: Does poor species-pair transfer conceal a partly stable community gradient?

**Audit date: 2026-10-28.** Entirely read-only on the frozen **66-pair** Snapshot Serengeti E7 CSV and its already-audited original result provenance. Both source outcomes were visible before defining this decomposition; **not a new independent field test, inferential model, ecological fit, or confirmation**. Original E4/E5/E7 fit/outcome decisions unchanged.

## General ecological question

The original Serengeti observation study found **23 of 46** comparable species pairs with concordant wet/dry shift directions between S01–S05 and S06–S11, and **zero** cross-period camera-deletion-stable diel rank reversals. The previous scalar-potential audit found that only **55.12% / 37.44%** of the discovery/validation squared-log-contrast energy was represented by an additive species vector.

**Does this near-zero pair-level transfer conceal two opposed statistical components?** A pair's observed seasonal log-diel shift is `y_ij^t`, where the same **46** comparable unordered edges and **11** connected taxa are used in both periods. Write its unique ordinary equal-pair-weight graph projection as

`y^t = G^t + C^t,     G^t_ij = beta_i^t - beta_j^t`

where `G` is the least-squares species gradient and `C` is its orthogonal residual in the pair graph's cycle space. With a connected graph of 11 taxa and 46 edges, the gradient has dimension **10** and the residual has dimension **36**. The previously reported **104** closed triangles are **redundant**, not 104 independent pieces of biological evidence.

## Exact frozen-aggregate results

| Cross-period geometry on identical 46 directed pair edges | Value |
|---|---:|
| Cosine of entire discovery vs validation pair-shift vectors | **+0.02963** |
| Cosine of species-gradient components | **+0.42627** |
| Cosine of pair-residual/cycle components | **−0.30959** |
| Full edge-vector cross-period inner product | **+1.27080** |
| Species-gradient contribution to that inner product | **+8.30559** |
| Residual-cycle contribution | **−7.03479** |
| Sum of last two values | **+1.27080** (exact projection identity) |

The cross-terms are **zero by linear-algebra construction**, not statistically estimated away. Thus in this fixed descriptive comparison, **positive alignment of the broad species-gradient component is nearly cancelled by negative alignment of the residual**, producing minimal overall angle alignment.

A leave-one-taxon-out sensitivity **recomputes the decomposition after deleting all edges containing that taxon**. The opposed gradient-positive/residual-negative structure survives **10 of the 11** omissions; **excluding spotted hyena** is the exception (both component cross-products become slightly positive). These are influential-species sensitivity checks, **not** 11 independent ecological replicates, resampling CIs or P-values.

### Can the discovery vector predict validation?

**No.** Against the no-change (`y=0`) validation vector baseline, using the **full discovery 46-pair vector directly** has squared-error skill **−2.3823**. Using **only its fitted species gradient** improves this particular descriptive score to **−0.7552**, but the skill is still **negative**. A positive gradient cosine therefore does not license an invariant species diel-trait law, a predictive transfer claim or an E4 model rescue. The residual/gradient partition uses an already exposed dataset and an outcome-informed common-pair graph.

## Critical falsification: triangle nonclosure requires no interactions, even with identical sites

We constructed a three-species A/B/C, **three-location** counterexample in which the **same three sites** contribute to every one of the three pair comparisons. At every individual site and for each species, **wet and dry have exactly the same night/midday record odds**. The only seasonal difference is a positive, species-by-site-specific multiplier that **scales each species' night and midday record counts equally**. Thus no species changes its within-site diel profile, and no three-way biological interaction is built into the synthetic data.

Nevertheless, separate species-pair Mantel–Haenszel aggregation creates seasonal log-odds changes:

| Synthetic pair | log(dry OR / wet OR) |
|---|---:|
| A–B | +0.61203 |
| A–C | −0.29534 |
| B–C | +0.69770 |

Triangle closure `delta_AB + delta_BC − delta_AC` equals **+1.60507**, rather than zero, *despite identical physical-site support and no true species-specific within-site diel shift*. The disparity arises from **noncollapsibility and changing pair-specific Mantel–Haenszel weights**, not a biological three-way interaction.

**Consequence:** E7's prior nonzero triangle closures (medians 0.851 and 0.708 log units) demonstrate **inexact algebraic representation of pooled pair summaries**, not ecological irreducibility, non-transitive competition or intrinsic three-species dynamics. Pair-specific site eligibility differences in E7 can add further problems but are **not even necessary** for this synthetic failure. Do not cite closure alone as a novel ecological mechanism.

## What can be concluded, and what would distinguish causes

The supported result is **two descriptive transfer components with opposite alignment, plus a decisive algebraic demonstration that pooled relational nonclosure is not diagnostic of biological interactions**. Neither component is inherently ecological: site/time mix, changing effective observation yield, taxon-by-environment variation, unequal site weights and real biological activity can all shape them. No new camera calibration, climatic covariates or direct passage denominator was examined here.

A future **mechanistic** ecology test would need (i) true common camera-year/phase support, (ii) an exposure-standardized within-cell species-by-diel model with **no MH-induced difference of weights between pairs**, (iii) independently declared environment modifiers and (iv) species-specific observation calibration or a defensible common-detection design. Note that at the exact site/year cell, pair log-odds derived from a single set of species record odds satisfy triangle closure **by definition even if ecological interactions exist**. Therefore closure/nonclosure cannot itself serve as a direct test for competition in either direction. Test environment-linked changes in those species odds instead.

### Audit lineage

- [Original E7 independent camera-network empirical study](E7_SERENGETI_WET_DRY_EMPIRICAL_SYNTHESIS.md).
- [Original 66-pair aggregate table](E7_RELATIONAL_PAIRWISE_66.csv), SHA256 `688bf6ff6d5289be6f577583f30a753f460bc53b03ca9c5d207a60f50d51951b`.
- [Earlier graph-coherence result](E7_RELATIONAL_COHERENCE_RESULT.json).
- [New frozen-aggregate deterministic audit](../../scripts/e7_pair_transfer_decomposition.py) with exact synthetic counterexample, regression tests and JSON result.
- Original E4 heldout scores not refitted; E5 original **0/17 qualified** and G4 unpassed; E7 original 11-season field endpoint unchanged.
