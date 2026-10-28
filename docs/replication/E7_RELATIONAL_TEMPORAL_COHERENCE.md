# E7 — Is recorded temporal community change a single species-specific axis?

**Post-outcome descriptive synthesis (2026-10-28).** This is a **model-free algebraic diagnostic**, using *only already-frozen E7 species-pair odds and supports* from the independently opened Serengeti 11-season empirical endpoint. No new wildlife rows or camera ZIPs, no E4 refit, no E5 detector calibration, no new inferential test. The hypothesis was framed **after** seeing 23/46 direction concordance; it is not an untouched prediction.

## Biological question

Is a shift in the relative timing of a recorded animal assemblage reducible to a persistent set of species-specific diel change scores, or does the measured community organization depend on **which species are compared and in what survey contexts**?

For each species pair i,j in the frozen E7 analysis, define:

\[
\delta_{ij}=\log\left[\frac{\mathrm{OR}^{\mathrm{dry}}_{ij}}
{\mathrm{OR}^{\mathrm{wet}}_{ij}}\right],
\]

where OR is the *camera-recorded* night/midday odds for taxon i relative to taxon j after matching physical camera site/hydrological year by the original method.

A **single transferable species-score representation** would imply:

\[
\delta_{ij}=\beta_i-\beta_j,\qquad \sum_i\beta_i=0.
\]

This requires exact triangle closure: \(\delta_{ij}+\delta_{jk}-\delta_{ik}=0\) for every three compared taxa. These identities are true of any pure species-potential differences; nonzero closure means the observed **pair-specific summary matrix** cannot be *exactly* represented as that one shared scalar potential.

**Crucial ecological limit:** Different pair estimates may use different eligible camera sets/years and different Mantel–Haenszel weights. Odds ratios are not generally collapsible across heterogeneous strata. Thus a violated triangle may arise from **site composition, camera observation and aggregation**, even if biological behavior were not intrinsically non-transitive. It is **not evidence of three-way ecological competition, a directed animal interaction, or causal temporal niche shifts**.

## Fixed source and matched support

- Original frozen [E7 empirical run 39222089646](https://github.com/zuizui0223/esdm/actions/runs/39222089646), JSON SHA256: `21a0b03d8c17442ddeeed79023ec28d23525c2815ca7a0bbaf54faec12e65f2a`.
- Its entire **66 unordered species pair** universe, including refused comparisons, is durably retained as [E7_RELATIONAL_PAIRWISE_66.csv](E7_RELATIONAL_PAIRWISE_66.csv), SHA256 `688bf6ff6d5289be6f577583f30a753f460bc53b03ca9c5d207a60f50d51951b`.
- The **same 46 estimable pair edges** are used in discovery and validation. They involve **11** of the original 12 taxa; *reedbuck* has **zero common estimable edges**. Do **not** assign it an artificial species score or imply the 12-taxon matrix is complete.
- Common pair support is connected among those 11 taxa. Fit a zero-sum species-potential gradient by **equal-pair-weight least squares** on those 46 edges, separately for each E7 partition. No weighting by individual camera-record counts or postresult selection of influential pairs.
- The fit criterion is `1 - Σ(δ_observed − δ_predicted)² / Σ δ_observed²`, compared to a **no-change (\(\delta=0\)) baseline**. It is a descriptive squared-log-contrast energy fraction, **not** an ordinary population-level ecological R².
- Test transferring the entire **discovery-estimated 11-species vector unchanged** to the *same* 46 pair edges observed in S06–S11; report its squared-error skill relative to no-change zero. No validation fitting, scaling, sign flipping or retuning of the discovery vector.
- Assess all **104 complete triangles** in this common pair graph in each partition. Triangles share edges and are **not independent** sampling replicates.

## Computed findings

| Fixed 46-pair common-support metric | Discovery S01–S05 | Validation S06–S11 |
|---|---:|---:|
| Taxa with shared comparison support | 11 | 11 |
| Scalar species-gradient squared-log-change energy captured | **55.12%** | **37.44%** |
| Unrepresented squared-log-change energy | **44.88%** | **62.56%** |
| Absolute triangle closure median, log scale | **0.8511** | **0.7080** |
| Complete species triangles | 104 | 104 |

**Out-of-period result:** applying the discovered species-potential vector *without adjustment* to validation pairs yields **skill −0.7552 relative to a zero-change prediction**: its squared error is **1.755×** the zero-change baseline. The already frozen pair effect sign agreement remains **23/46**. This does not establish impossibility of *any* environmental or re-scaled species-conditional prediction; it rejects safe direct transplantation of this particular descriptive unconditioned scalar-gradient summary to the later collection seasons.

The triangle closure medians correspond to unclosed multiplicative contrasts around `exp(0.8511)≈2.34` and `exp(0.7080)≈2.03`, **not** a species abundance effect, competition strength or sensor detection parameter. Nonzero closure can be a normal consequence of different observational matching and MH weighting among pairs. We did not calculate P-values or treat 46 edges/104 cycles as independent biological replicates.

The original field result remains the one in [E7_SERENGETI_WET_DRY_EMPIRICAL_SYNTHESIS.md](E7_SERENGETI_WET_DRY_EMPIRICAL_SYNTHESIS.md). This post-outcome diagnostic quantifies **why collapsing those pair summaries into one species-wise number would lose important recorded contextual structure**. It does not establish *which* environmental interaction (rainfall, vegetation, migration, habitat, camera effort, detector behavior) supplies that residual.

## Ecological implication and next independent test

The strongest general statement is **bounded and conditional**: *in these sampled camera networks, species-relative recorded diel changes cannot be summarized exactly by an invariant species-only seasonal axis and the one fitted summary does not predict later seasons*. A more informative biological prediction is **environment-specific temporal assembly**, not a universally conserved pair ranking:

\[
\log q_i(s,t)\;=\;\alpha_i + \gamma_i^\top X(s,t) + u_i(s,t)
\]

where `q` must distinguish true passage/activity from observation-process yield, and `X` might include objectively measured precipitation, vegetation phenology and survey exposure. This is a **future conceptual model**, not a fit or ecological mechanism demonstrated here. It should be tested with *new* heldout observations, pre-fixed ecological drivers, **shared site-by-season support** and, where possible, independent taxon-specific detector calibration.

**No new E8 model generation, E4 rescue, E5 qualification or repeated opening of Serengeti biological records is authorized by this document.** E4 frozen activity score and E5 0/17/G4-stop status are unchanged.

## Reproducibility

The read-only script [scripts/e7_relational_coherence.py](../../scripts/e7_relational_coherence.py) verifies both original summary and compact 66-pair data hashes, checks the exact pair-table derivation if provided with the GitHub Actions original artifact, rejects disconnected common-support graphs, calculates the zero-sum species-potential by a deterministic 11×11 linear solve, and records all species scores and triangle summaries in [E7_RELATIONAL_COHERENCE_RESULT.json](E7_RELATIONAL_COHERENCE_RESULT.json). Synthetic exact-transitivity and broken-transitivity cases are tested separately. No biological archive, raw camera site names or individual images enter the calculation.


### Independent algebraic counterexample to overinterpreting nonclosure (2026-10-28)

A [separate frozen-aggregate transfer audit](E7_PAIR_TRANSFER_COMPONENTS_AND_NONCOLLAPSIBILITY.md) decomposed the same 46-edge vectors into species-gradient and orthogonal residual/cycle components. Their **discovery–validation cosines were +0.426 and −0.310**, respectively, nearly cancelling the whole-vector **+0.030**. This is an exact descriptive decomposition, **not** a transfer of underlying species activities.

More importantly, a synthetic dataset with **exactly the same three sites for all three species pairs** and **no wet/dry change in any species' night/midday odds at any site** produced an aggregate Mantel–Haenszel triangle closure error of **+1.605 log units**. Thus *even pairwise camera-site overlap does not by itself rescue an ecological interpretation of pooled triangle nonclosure*: changing aggregate weights and noncollapsibility can create it without biological interaction or a shift in species diel profiles. The original 104 triangles span at most a 36-dimensional residual cycle space on the 46-edge, 11-species connected graph. No new Serengeti biological records were reopened.
