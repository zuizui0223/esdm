# E5 ecological mechanism: conditional sensor performance versus behavioral composition

**Date:** 2026-10-08. **Status:** explanatory hypothesis and inspectable mathematical decomposition, not an empirical positive finding, an outcome respecification, or a new candidate-screening gate.

## Why the current E5 null/hold does not settle the ecology

- The original direct-detection E5 has **0/17 qualified public-data candidates**. Its most substantial completed alternative, the Wolfson wild-pig GPS-anchored geographic transfer, is **UNRESOLVED** with a sample-identity quality HOLD; the original one-shot outcome is never rerun or reclassified.
- Rhode Island preserves individual camera-member IDs and ample site replication, but 50–100 m separated camera members do not create a known shared-passage denominator. Independent activity and common effective detection remain structurally confounded.
- Findlay, Briers & White (2020) **directly observed passes via continuous CCTV** in two small studies and estimated stages of camera detection conditional on a pass. Their analysis reports that distance and faster gait alter trigger/registration, with distance effects in opposite directions for the two stages. The source code separately models `TRIGGER` and conditional `CAPTURE`; the E5 donor assessment pins its repository without opening the CSV biological rows.
- Jumeau, Petrod & Handrich (2017) independently compared continuous video and camera traps in three wildlife underpasses. They report missing **43.6%** of small-mammal events and **17%** of medium-sized-mammal events, and the estimated entry/refusal behavior was misclassified in **40.1%** of cases. This is evidence that the observation process can distort behavior classifications, but not a test of spatial transportability.

Sources: [Findlay et al. 2020](https://doi.org/10.1007/s13364-020-00478-y); [Findlay public code](https://github.com/melaniefindlay/CT-Detection/tree/abc72f535bb59ebed202fb7acca852fc1647e97a); [Jumeau et al. 2017](https://doi.org/10.1002/ece3.3149).

## A falsifiable mechanism, not a stationary correction factor

At geography/season regime `r`, detector location `s` and diel time `t`, define:

- `A_rs(t)`: *actual passage intensity through the camera's reference zone* (not regional abundance or GPS speed);
- `f_rs(z|pass,t)`: distribution of passage covariates `z` (speed/gait, distance/trajectory, body/thermal state, habitat and environmental context) **among actual passes**;
- `p_T(z,t,r,s)`: probability of a sensor trigger conditional on a known passage;
- `p_R(z,t,r,s)`: probability of a usable registered image conditional on both passage and trigger;
- `E_rs(t)`: operational exposure; `C_rs(t)`: expected number of recorded passages.

Then

```
C_rs(t) = E_rs(t) * A_rs(t) * D_rs(t)

D_rs(t) = integral f_rs(z | pass,t) * p_T(z,t,r,s) * p_R(z,t,r,s) dz
```

In this definition, **effective diel detection `D` can vary even when the underlying conditional sensor-stage functions are unchanged**: the mix of passage speeds/distances may change by time, site or season. The reverse can also hold: large changes in the two stage probabilities can partially cancel, so the overall recorded-event curve appears stable.

Thus a camera-vs-telemetry mismatch is not automatically a fixed hardware effect, and a failed marginal correction transfer does not prove nontransferability of the conditional detection functions.

### Exact, symmetric two-regime decomposition

Compare two regimes at the **same diel time** on a common predeclared covariate domain `z`. Let `p_r(z)=p_{T,r}(z)p_{R,r}(z)` and `D_r=∫f_r p_r dz`. Then

```
D_2 - D_1 = MECHANISM + COMPOSITION

MECHANISM   = (1/2) * integral (p_2 - p_1) * (f_1 + f_2) dz
COMPOSITION = (1/2) * integral (f_2 - f_1) * (p_1 + p_2) dz
```

This symmetric decomposition is an algebraic identity; it is **not causal identification**. `MECHANISM` here is only a descriptive change in the measured conditional detector-stage response. `COMPOSITION` is only a descriptive change in passage-covariate distributions. Unmeasured covariates, imperfect CCTV, lack of common support, calibration error, and site/individual selection can invalidate practical attribution.

An inspectable pure-Python function lives at `scripts/decompose_e5_detection_composition.py`. It takes no empirical source and fits nothing; the tests verify only the identity and no-transfer implication under fixed conditional detection.

## Distinguishing empirical predictions

**P1 — Conditional stability, marginal nonstationarity.** After conditioning on matched known-pass speed/distance/geometry and camera settings, `p_T` and `p_R` may transport across contexts better than raw marginal `D_r(t)`; strong variation in `f_r(z|t)` alone may account for changes in marginal diel detection. This predicts a measurable reduction of out-of-geography calibration error upon standardizing passage composition **without choosing covariates after seeing the outcome**.

**P2 — Apparent activity inversion.** If the day/night ratio of `D_r(t)` changes enough to oppose the true passage day/night ratio, the camera time-density can exhibit a trend opposite to the pass-reference curve. This is a *possibility*, not a claim that it occurred in Wolfson, Rhode Island, Findlay, or Jumeau.

**P3 — Stage compensation.** Trigger sensitivity and conditional registration can respond to distance in opposing directions; their product can change less than either stage. Direct stage-labeled CCTV evidence can distinguish compensation from a stable all-in detection probability.

## Required decisive data; no post-hoc rescue

A valid future test needs a shared-passage denominator from continuous reference observation or an independently calibrated equivalent, **including missed camera detections**; individual physical camera/deployment IDs; contemporaneous pass timestamps; measured passage speed/distance/trajectory or prespecified proxies; trigger and registered-image outcomes; effort and device/settings; and genuinely crossed geography/season replication. The original E5 contract additionally requires independent 20/10 training/heldout sites and six months per split, unless a different *new* research route is explicitly defined in advance.

Critically, the published Findlay reference design has too few sites, too little time and confounded species/context to perform this E5 transfer test. Jumeau likewise has too few crossings, and availability of aligned event-level rows was not verified. Neither licenses imputing `D(t)` into wild-pig or Rhode Island data; **there is no new empirical result or E5 G4 promotion**.

The substantive ecology target is not “cameras are biased” (already known) but **whether context-dependent animal behavior drives changes in what the same observation process sees**. Testing that proposition requires new independent passage-calibrated, geographically crossed evidence.
