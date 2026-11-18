# What can eSDM learn about a species pool, site state, and camera observation from records alone?

**2026-11-18 · exact response-free submodel audit · NOT an empirical result or new fitted esdm generation**

## Why this is the next bottleneck

The repo's existing spatial studies measure different targets. Safari14 reports **recorded reserve sorting** against a camera-/species-incidence fixed-margins null (PR #232), not detection-corrected source-pool filtering. The independent CamTrapAsia C1 test reports **negative heldout incremental prediction** from the frozen environmental distance (PR #234; `MAE_G - MAE_G+E = -0.003080`), not the absence of environmental sorting. The independent NEON C2 programme stopped on a taxonomic-class conflict **before estimating any mammal-assemblage effect** (PR #235). E4's original activity knockout remains negative on its east-heldout MICA endpoint; E5 remains **0/17 qualified**. None of those studies jointly measures regional species pool membership, local use, independent animal passages and focal camera failures.

The question here is deliberately *structural*: **Does adding a spatial latent field or repeated camera records suffice, in principle, to identify each ecological and observational process?** A minimal counterexample says **no, not without additional independent structure or evidence**. This audit describes exactly the submodel for which that conclusion is valid; it does not claim that every hierarchical occupancy model is unidentified.

## Explicit minimal observation model

For **one region × species × sampled site**, let:

- `R ~ Bernoulli(rho)` be a latent regional-availability gate;
- `Z | R ~ Bernoulli(R * psi)` be persistent site occupancy / use, conditional on regional availability;
- `A_t | Z ~ Bernoulli(Z * a)` indicate whether an occupied site is accessible/passed through the camera zone at occasion `t`;
- `Y_t | A_t ~ Bernoulli(A_t * p)` indicate whether an available animal is correctly registered by the camera.

Assumptions: **no false-positive species labels**, complete/known effort for the occasions, common parameters inside this stratum, closure of `R` and `Z` during the repeated survey, and conditionally independent occasion-level `A_t`/`Y_t` given `Z`. The four parameters are strictly between zero and one. `A_t` is an **occasion-varying availability** gate, not an independently verified animal passage. The meaning of occupancy is *camera-site use under the declared period*, not whole-region animal abundance.

Define `q = rho * psi`, `d = a * p`. For a binary history `y = (y_1,...,y_T)` with `k` positive registrations, its *exact marginal likelihood* is:

- if `k > 0`: `P(y) = q * d^k * (1 - d)^(T-k)`;
- if `k = 0`: `P(y) = 1 - q + q * (1 - d)^T`.

Therefore all distributions of camera detection histories for **any number of temporal revisits** depend on **only `q` and `d`**, not on four free parameters independently. This is a structural equivalence result for a **one-site (or independent site-specific pool gate) submodel**. With **a shared region-level R across many independently replicated sites**, cross-site covariance can in principle provide additional information under an explicit multi-scale hierarchy, so do **not** generalize this proof to a full crossed multi-region design. Spatial/hierarchical priors can also regularize estimates; regularization is not by itself independent empirical identification of a parameter.

### Exact counterexample: all observation histories coincide

| Hidden gate | Case A | Case B |
| --- | ---: | ---: |
| Regional pool `rho` | 0.60 | 0.80 |
| Local occupancy `psi` | 0.80 | 0.60 |
| Per-occasion availability `a` | 0.50 | 0.75 |
| Camera registration `p` | 0.60 | 0.40 |
| Composite `q` | **0.48** | **0.48** |
| Composite `d` | **0.30** | **0.30** |
| Single-visit registered fraction `q*d` | **0.144** | **0.144** |

The exact 2-occasion distribution for either case is: `P(00)=0.7552`, `P(01)=P(10)=0.1008`, `P(11)=0.0432`. Code checks **every** binary history, not just aggregate detections, at `T=1,2,3,6,10`. The maximum discrepancy is below machine tolerance. This is a **mathematical equivalence**, not a stochastic simulation or a model-fits comparison.

## What a stronger design actually identifies

When 2+ truly independent conditional detection occasions are available at many sites sharing the same parameters and the closure assumption holds, the **population probabilities** `P(11) = q*d^2` and `P(10) = q*d*(1-d)` imply:

```
d = P(11) / (P(11) + P(10))
q = (P(11) + P(10)) / d
```

This can identify *composite site-use `q`* and *effective per-occasion recording `d`*, not the four elementary factors. These are population probabilities, **not estimates obtainable from one site's two binary records alone**; rare species, autocorrelation, incomplete effort and violation of closure may make identification practically poor or invalid. Even a large number of independent temporal revisits cannot separately estimate `rho` versus `psi` or `a` versus `p` within the declared minimal model.

An **independently validated reference-passage denominator and known camera/reference overlap** may anchor `p`, allowing `a = d/p`. This does *not* split `rho` from `psi`. An **independently verified regional pool**, or externally identified pool probability `rho`, can anchor that factor, allowing `psi = q/rho`. This does *not* split `a` from `p`. Together with valid repeated occasions, **both exact anchors** permit algebraic recovery of all four gates in the idealized model, but *having a range-map prediction is not equivalent to knowing `rho` exactly*, nor is a second motion-triggered camera necessarily an independent denominator of passages that both devices missed.

### Dataset requirements, not another v0.7/v0.8 model generation

| Evidence class | What it can support | What it does **not** support on its own |
| --- | --- | --- |
| Single camera-positive incidence snapshot | Combined detected-record probability `rho*psi*a*p` | Any separate ecology-versus-detection process |
| Known operating effort + conditionally independent repeated camera occasions | `q=rho*psi` and `d=a*p` under closure, no false positives | Regional source pool vs local state; true animal availability vs detector yield |
| **Independent, non-trigger-selected known passages**, overlapping intervals and calibrated reference sensitivity | Camera registration `p` conditional on a measured passage within the shared zone | Independently verified regional species pool |
| Independent, validated species pool / range source with explicit uncertainty | Constraints on `rho` or fixed eligibility; source-pool contrasts | Camera registration `p` or species-specific event detection by itself |
| Geographic × camera/protocol crossing and truly unopened geographic holdout | Source-transfer assessment once competing models are frozen | Causal habitat filtering, general process superiority, or full identification by design label alone |

The original [independent reference-passage protocol](INDEPENDENT_REFERENCE_PASSAGE_AND_ECOLOGY_PROTOCOL.md) already requires passage IDs, camera and reference overlap, non-trigger-selected observations, and reference-integrity checks. Reuse that contract rather than redefining an easier G4 threshold. The separate [E5 external-activity-anchor proof](E5_EXTERNAL_ACTIVITY_ANCHOR_IDENTIFICATION_RESULT.json) identifies only **relative** diel distortion shape, not absolute detector sensitivity; this new audit does not convert that into an absolute calibration.

## Next empirical decision (separate, genuinely independent evidence)

The most defensible future field question is not another post-hoc beta-diversity threshold. In a new independent source, collect or identify **(i)** prospectively bounded, independent regional species-pool information; **(ii)** repeated camera occasions and verified operating-day effort with ecological closure windows; **(iii)** a subset of *independently* recorded passages through the same known camera zone (including camera misses) with reference sensitivity documented; and **(iv)** a crossed geographic/protocol holdout. Only after response-blind checking these four evidence channels should a new fit compare pool/state/detection components and ecological claims. If only the first two are present, analyze the identifiable composites `q` and `d`, not four purportedly identified causes.

Do not select a new source because it yields a favorable coefficient. Do not reopen Safari14, C1 or C2 to rescue a mechanism. **No new wildlife data were opened or fit here, no ecological positive result was claimed, and E5 remains G4-unpassed (0/17).**

## Related methodological literature

- MacKenzie-style repeated-visit occupancy/detection separation and integrated multi-species occupancy: https://doi.org/10.1111/2041-210X.13811
- Multi-scale occupancy, regional versus local site availability: https://doi.org/10.1002/jwmg.245
- Camera availability/site use and autocorrelation pitfalls: https://doi.org/10.1111/2041-210X.14359
- Temporary availability can bias single-scale occupancy interpretation: https://doi.org/10.1111/2041-210X.13881

This elementary identification audit is a **constraint check within established occupancy theory**, not a claim to have invented multi-scale occupancy modelling.

## Reproduce

```
python -m pytest -q tests/test_pool_state_detection_identification.py
python -m scripts.audit_pool_state_detection_identification --out docs/replication/POOL_STATE_DETECTION_IDENTIFICATION_RESULT.json
```

The result JSON is deterministic, source-free and deliberately denies E5 qualification or eSDM empirical superiority. Existing V04-R5b, E4, E5, E7, Safari14, C1 and C2 receipts are untouched.
