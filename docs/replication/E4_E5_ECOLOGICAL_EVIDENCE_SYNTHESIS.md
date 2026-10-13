# ESDM empirical synthesis: ecological activity versus the observation process

**Evidence snapshot:** 2026-10-13. **Status:** cross-programme scientific synthesis of immutable results. This document introduces **no new fit, reclassification, candidate qualification, or post-outcome parameter tuning**.

## Research question

**Does a structured ecological activity term transfer to a new survey domain, and can a changed observed diel pattern be attributed to ecological behavior rather than how animals were recorded?**

The ESDM generative distinction is:

\[
\text{ecological state} \longrightarrow
\text{passage/activity} \longrightarrow
\text{observation/recording} \longrightarrow \text{data}.
\]

For cameras at site \(s\) and diel time \(t\), a useful observation accounting equation is

\[
E[Y_{s,t}] = E_{s,t}\, A_{s,t}
\int f_{s,t}(z\mid\text{pass})\,
p_{T,s,t}(z)\,p_{R,s,t}(z)\,dz.
\]

Here \(E\) is actual deployed effort, \(A\) is true passage intensity in the sampled field of view, \(f\) is the distribution of movement, trajectory, distance, etc. among actual passes, \(p_T\) is the trigger probability given a pass, and \(p_R\) is usable registration conditional on a trigger and pass. This is **conceptual bookkeeping, not a claim that any E4/E5 study estimated all these factors**. Broad regional abundance and local passage intensity are different quantities.

## Four independent pieces of evidence

| Programme/source | What was empirically evaluated | Result | Evidence limit |
|---|---|---|---|
| **E4 / MICA muskrat** | Frozen full state/activity model against independent activity/state knockouts on 733 east-heldout deployments | Mean activity transfer gain **−0.639051** log score; physical-location block 95% interval **[−1.2594, −0.0187]** | Predictive non-generalization is supported **for this frozen endpoint**; cannot attribute the failure to animal behavior vs survey/source detection |
| **E4 / network diel audit** | Night/day event-rate contrast and nonfocal taxa in the same observation network | Annotated-training night/day rate ratio **13.40**, heldout D-stratum **2.96**; **6/7 eligible nonfocal species** shifted to lower heldout ratios | A **cross-taxon observed-pattern shift**, not independently known behavior, protocol bias, or a causal eastward ecological change |
| **E5 alternative / Wolfson wild pig GPS + cameras** | Frozen 8 symmetric cross-geography transfers of effective diel camera-observation distortion, calibrated only relative to GPS movement/activity | Median gain **+0.007876**, **6/8** positive; 1,000-bootstrap interval **[−0.05019,+0.03125]** ⇒ **UNRESOLVED** | California summer reports **434** LocationName labels against **48** reported physical cameras; **383** summer singleton labels; **194** California winter rows without site ID ⇒ cluster bootstrap QC HOLD |
| **E5 descriptive donor / Findlay known CCTV passes** | Trigger and usable-image registration stages in released fox/badger passages | Fox lateral passes: near ≤1 m trigger **55/88 = 62.5%**, registration **19/55 = 34.55%**, recorded/pass **19/88 = 21.59%**; far >3 m trigger **47/175 = 26.86%**, registration **27/47 = 57.45%**, recorded/pass **27/175 = 15.43%** | Source tables align in **881/881 row order**, but **no independent unique passage ID**; near/far comparison is retrospective/descriptive, has no authorized CI, and is **not** geographic or diel transfer |

**Additional E4 result:** State knockout gain **+0.008391** was a small descriptive positive point estimate, but physical-location resampling gave **[−0.01895,+0.03573]**; it is **not** robust confirmatory support for the ecological state channel. Among the **128** heldout deployments containing focal events, **127** favored the activity knockout. The 605 zero-event deployments mostly contributed tiny positive activity gains. The source-stratum and geographic extrapolation are strongly confounded: the heldout D-prefixed stratum contained about **99.0%** of focal events, and its contribution to negative activity loss was overwhelming. Removing it descriptively leaves a mean activity gain around **−0.0031**, so avoid universalizing the large aggregate −0.639.

**Findlay stage logic:** Near-to-far trigger probability falls, while registration **conditional on being triggered** rises. The two stages have opposite log changes (−0.8446 and +0.5086); the composite still decreases (−0.3361 log change, approximately 28.5% lower far than near). The increase in registration among triggered events can arise from **selection of which passages trigger**; it is not a demonstrated improvement of the hardware or a causal compensation mechanism. For badgers in the far bin, 16 triggered CCTV passages versus 15 registration-eligible rows remain a frozen cohort mismatch. An exploratory sensitivity record shows **hypothetical** substitutions k=4/k=6 could erase two fox comparisons, but the observed number of linkage errors was never estimated.

**Findlay row-order audit:** Pinned fox/badger files each contain **881** rows; all 881 match in row order on the predeclared shared attributes and trigger flag. Only 530 fingerprint rows are unique; 351 rows share repeated attribute combinations. This supports consistent source-table extraction but does not provide an externally documented, immutable per-pass identifier. It does not retroactively convert the descriptive FOX calculation into confirmatory evidence.

## Three distinct scientific judgments

### 1. Supported: a particular stationary ecological activity channel failed predictive transfer

The E4 full model was materially worse than the activity knockout under its declared geographic+survey-domain holdout. The negative direction persisted under **27-physical-location clustered uncertainty**, not just 733 deployment-level resampling. It is a defensible **ecological model result**: stationary modeled diel-activity information cannot be assumed to generalize across this shift.

It is **not** evidence that muskrat activity does not exist, that ecology is irrelevant, or that animals necessarily shifted behavior eastward.

### 2. Observed: the process converting passages into camera records has multiple consequential stages

A continuous-CCTV known-pass reference can measure *misses* and estimate trigger and registration separately; Findlay's source supplies a concrete empirical case. In its fox contrast, the stages move in different directions with passage-distance group, leaving a composite with a different magnitude. This supports separating observation processes when interpreting ecological diel maps; however, such detection-stage distance effects were already considered in the original publication and are **not new causal discoveries by ESDM**.

### 3. Still unidentified: what caused the MICA shift, and whether detection corrections transfer

E4 has no independent per-pass reference for its annotated observation stream, so its observed cross-domain diel change cannot be partitioned uniquely into animal activity versus detection/annotation. The wild-pig transfer was UNRESOLVED and sample-ID compromised. Rhode Island retained camera-member IDs and extensive paired deployments but separate cameras tens of metres apart did not create independently identified shared-passage detection; original E5 **G4 failed for that released design**.

The three studies **must not be pooled** into a numerical test of one common detection parameter: they differ in taxa, camera architecture, reference denominators, geography and season.

## Hypotheses that remain genuinely ecological and falsifiable

**H1 — Passage-composition mediation.** Diel or geographic changes in distance/gait/trajectory distributions **among actual passes** can shift marginal observed camera time profiles even if conditional \(p_T(z)\) and \(p_R(z)\) are unchanged. Test with independent known-pass recording and predeclared behavioral covariates at shared sensor deployments; standardize passage composition and evaluate strictly heldout regions.

**H2 — Conditional detector portability versus marginal detector nonstationarity.** Across geographically crossed camera settings, behavioral-conditional trigger/registration functions may transfer better than raw marginal effective detection. This requires independent pass denominators, common support in \(z\), and enough matched devices/protocols across regions; it **cannot** be inferred from the current Wolfson or Rhode Island data.

**H3 — Observed diel inversion.** An apparent observed night/day shift could oppose a reference passage night/day shift if the effective observation probability changes sufficiently by time. A genuine test needs time-stamped **missed and recorded** passages, not camera events alone. No supplied E5 dataset has demonstrated such an inversion.

These are **future hypotheses**, not positive results.

## What would count as decisive E5 evidence

A new geographically crossed reference-camera design should provide, before response selection:

1. Physical deployment and camera/device identities, explicit operational effort, and independent known-pass records **including misses**;
2. Persistent passage identity, day/night timestamps, passage distance/trajectory/gait and separate trigger and registration outcomes;
3. Shared/crossed camera/source protocols in at least two geographies, independent physical-site sample sizes at least 20 training and 10 heldout, and **at least six distinct valid calendar months per geographic split** under the original frozen E5 standard;
4. A structural argument showing how the common diel detection component is identified, not only relative differences between two cameras;
5. Pre-outcome freeze of region/source × diel and season × diel terms, negative controls, geography holdout, a suitable location-cluster uncertainty unit, and performance metric.

If such independently calibrated and crossed data are unavailable, **the correct scientific result is refusal to identify the cause**, not another synthetic generation, another optimistic inference backend, or a post-hoc reanalysis of E4.

## Publication-ready conclusion, bounded by the evidence

> Under the frozen MICA domain transfer, adding an explicit stationary diel-activity component worsened heldout predictive performance, robustly across physical locations. Observed day/night changes also appeared across multiple taxa, implying that the shift cannot be regarded as a demonstrated focal-species behavioral change. Separately, a known-passage CCTV dataset showed that triggering and usable-image registration can vary in opposing directions, demonstrating why one marginal camera-record curve conceals multiple observation stages. However, current independent public datasets did not identify the cause of the MICA transfer failure or establish portable diel detection correction. The strongest conclusion is therefore a boundary on ecological attribution under nonstationary observation, together with an experimentally testable path for crossing that boundary.

Do **not** promote this to a claim of causal behavior, E5 original G4 qualification, proof that all detection mechanisms fail to transfer, state-process confirmation, or a new species-specific ecological law.

## Immutable evidence

- E4: [frozen result](E4_MICA_SPARSE_FROZEN_RESULT.json), [post-result synthesis](E4_MICA_POSTRESULT_SYNTHESIS.json).
- Wild pig: [frozen outcome receipt](E5_WILDPIG_ACTIVITY_ANCHOR_OUTCOME_RECEIPT.json), [camera-site QC](E5_WILDPIG_CA_LOCATIONNAME_QC_RESULT_RECEIPT.json), [interpretation](E5_WILDPIG_CA_LOCATIONNAME_TERMINAL_INTERPRETATION.md).
- Rhode Island: [deployment geometry](E5_RHODE_ISLAND_DEPLOYMENT_GEOMETRY_RECEIPT.json), [G4 refusal](E5_RHODE_ISLAND_GEOMETRY_TERMINAL_INTERPRETATION.md).
- Findlay: [stage counts](E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json), [row-order audit](E5_FINDLAY_PASSAGE_LINKAGE_FORENSIC_RECEIPT.json), [linkage sensitivity](E5_FINDLAY_PASSAGE_LINKAGE_SENSITIVITY_RESULT.json).
- E5 specification: [unchanged qualification contract](E5_INDEPENDENT_ACTIVITY_DETECTION_QUALIFICATION_CONTRACT.json); **0/17 full standard-qualified candidates**.

All underlying one-shot outputs remain frozen, and there is no authorization in this synthesis for new biological value openings, model fitting or reruns.
## Follow-on descriptive diel-attribution frontier (2026-10-13)

Using **only the frozen E4 post-result aggregate ratios**, the observed night/day contrast is 13.4048 in annotated training and 2.9645 in heldout D: a ratio-of-ratios of **0.22116**. Algebraically, this equals the cross-cohort *true reference-zone passage* diel-ratio change multiplied by the cross-cohort *effective observation* diel-ratio change. Their individual contributions are **not identified**. [The read-only scenario calculation](E4_E5_DIEL_ATTRIBUTION_FRONTIER.md) gives the exact counterfactual factor pairs and the missing known-pass calibration target; it introduces no model fit, independently estimated detection factor, causal claim or E5 G4 promotion.
