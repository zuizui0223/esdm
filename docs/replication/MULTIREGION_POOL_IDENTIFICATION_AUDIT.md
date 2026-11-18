# Exact multi-region, multi-site identification: when a shared species-pool state can be distinguished

**2026-11-18 — response-free methodological extension of PR #236.** No wildlife image, event, sequence, site count or response was opened. This is a simple constructive identification result *within established multi-scale occupancy theory*, not a new fitted eSDM generation or a novel universal theorem. All prior ecological outcomes remain unchanged.

## Why this follows Safari14, C1, C2, C3

- Safari14: observed mammal-label sorting exceeds a **fixed camera-row and taxon-column incidence null**, but detection-corrected occupancy and ecological cause are unknown.
- CamTrapAsia C1: frozen environmental distance **did not** improve new-landscape Brier/MAE-equivalent *in its own separate model* (the actual frozen metric was MAE gain −0.003080); no causal absence of IBE was established.
- NEON C2: stopped **before estimating an effect** because one binomial had conflicting taxonomic classes.
- Snapshot Europe C3: official source authenticated, but the one-shot empirical run **stopped before opening a single sequence** because the same camera *hardware* identifier mapped to different country/array units (`RESPONSE_SCHEMA_STOP`). No 2021→2022 Brier scores were estimated.
- PR #236: showed that a **one-site** camera-history model depends only on `q=rho*psi` and `d=a*p`, hence **four elementary gates are not recovered** by temporal repetition alone. That audit expressly warned its counterexample did not prove nonidentifiability in a shared-region, multi-site hierarchy.

This audit resolves that limited open question **constructively**: with a *shared* region-level availability state, multiple sites and repeated visits, the first **three** levels (`rho`, `psi`, and *effective* `d`) can be separated in population moments under strong homogeneity/independence assumptions. Camera availability `a` versus conditional registration `p` **still cannot be separated without an external identifying channel**.

## Exact hierarchy and conditional independence

For each independent replicate region `r` and focal species (or an exchangeable class of region–species replicates), assume:

1. `R_r ~ Bernoulli(rho)` is **shared by every site in that region** for that species. It represents source-pool availability and is constant for the chosen closure window.
2. `Z_{ri} | R_r ~ Bernoulli(R_r * psi)` is the site-level occupancy/use state. Site states are independent **conditional on** the shared regional gate.
3. At each declared equal-effort occasion `t` at an occupied site, `A_{rit} ~ Bernoulli(a)` is temporary animal availability in a known focal zone, independent across occasions **conditional on Z**.
4. `Y_{rit} | A_{rit} ~ Bernoulli(A_{rit} * p)` is correctly registered camera presence, with no false-positive taxon classifications, and no unobserved shared camera, season or animal-behaviour shock.

Parameters are *homogeneous and strictly interior* (`0 < rho,psi,a,p < 1`) across independent replicate regions/sites/occasions in this elementary proof. Define `d=a*p`.

Three **population joint probabilities** contain the identifiable moment information:

```
m1     = P(Y_r,i,1=1)                    = rho * psi     * d
m_same = P(Y_r,i,1=1, Y_r,i,2=1)       = rho * psi     * d^2
m_cross= P(Y_r,i,1=1, Y_r,j,1=1), i!=j = rho * psi^2   * d^2
```

Thus, whenever these moments are positive and compatible with the assumed model:

```
d   = m_same / m1
psi = m_cross / m_same
rho = m1^2 / m_cross
```

The cross-site probability `m_cross` contains **shared region-level variation** that a one-site camera history cannot reveal. The elementary single-site and cross-site null spaces are different. By contrast, any replacement `(a,p) → (k*a,p/k)` remaining inside `(0,1)` leaves **every observed camera history unchanged**, even with arbitrarily many regions and sites when only camera outputs enter the likelihood.

If **independently verified passages** through the same zone estimate the conditional registration probability `p` (with known camera/reference overlap and a validated reference system), `a=d/p` can be recovered algebraically in this idealized model. An auxiliary channel without independently known misses does *not* identify `p`.

## Exact numerical certificate (not a simulation)

| Gate | Case A | B: same 4-bit camera distribution | C: same one-site composite only |
| --- | ---: | ---: | ---: |
| Region availability `rho` | 0.60 | 0.60 | 0.80 |
| Conditional site use `psi` | 0.80 | 0.80 | 0.60 |
| Occasion availability `a` | 0.50 | 0.75 | 0.50 |
| Camera registration `p` | 0.60 | 0.40 | 0.60 |
| Composite `rho * psi` | 0.48 | 0.48 | 0.48 |
| Composite `a * p` | 0.30 | 0.30 | 0.30 |
| `m_cross` | **0.03456** | **0.03456** | **0.02592** |

For case A, `m1=0.144` and `m_same=0.0432`. All **16 possible binary records** from two sites × two occasions are enumerated exactly (floating-point roundoff below 1e−12). Case B has the same full distribution as A despite different animal availability and camera registration; C has the same one-site observation law, but a distinguishable **cross-site** distribution under the shared-region assumption.

An exact rational *log-moment* Jacobian has columns `[log rho, log psi, log a, log p]`:

```
          rho psi  a  p
m1          1   1   1  1
m_same      1   1   2  2
m_cross     1   2   2  2
```

Its rank is **2** when only the first two (single-site) moments are available, **3** when cross-site dependence is included, and **4** after adding an independent `p` reference row `[0,0,0,1]`. This is an **algebraic structural rank** statement, not an empirical power calculation or a claim of posterior precision.

## Field requirements and hard refusals

The moment identities are **population probabilities**. A single region with two cameras, each recorded twice, cannot estimate `rho` with meaningful precision. The design needs **many independent region or region–species replicates** with a scientifically justified common parameterization, at least **two independently located sites** per replicate region, and **two or more genuinely independent occasions** at each site. A site is a mapped **station/observable zone**, not a camera hardware serial number; camera hardware may move, as the C3 source contract stop demonstrated.

The following break this exact calculation or its interpretation:

- `R` is independent at each site (rather than shared within a region): then `m_cross=m1^2`, the formula spuriously gives `rho=1`, regardless of true availability.
- Location/site heterogeneity in `psi` or `d`, unequal unmodelled observation effort, habitat/camera protocol confounding, or species-specific taxonomic false positives: the homogeneous factorization is invalid.
- Temporally autocorrelated movement or trigger bursts: `m_same` is not generally `rho*psi*d^2`. Site-use and detection inference may be biased or overconfident.
- Sites are not independent conditional on the regional gate (shared individual ranges, common weather, detector effects): `m_cross` is no longer solely a regional-pool signal.
- Regional/species replicates are not exchangeable: estimates from pooled moments need a new, prospectively fixed hierarchical model rather than the three closed-form ratios.
- A camera's deployment ID is absent or conflates a moved device with a stable station: **stop on observational-unit identity before reading species values**. A new question would require separately frozen, evidence-backed station mapping, not retroactively repairing the consumed C3 outcome.

No design change or sensitivity can turn this response-free proof into an E5 G4 pass; the frozen E5 registry remains **0/17** standard-qualified. The target of E5 is still geographic × protocol crossing **and an independently identifiable detection channel**, plus physical and temporal support. Nor is this a demonstration of eSDM superiority over a conventional occupancy model.

## Decision for next empirical work

We should not do an additional outcome-dependent rerun of Snapshot Europe C3. Instead, require a **response-blind observational-unit contract** for a different, unopened dataset that explicitly contains:

- an independently documented camera **station/deployment** crosswalk (never infer station solely from hardware ID), start and stop timestamps, observation zone and source/protocol identifiers;
- replicated physical sites nested in identifiable region/source-pool strata, with *independent* occasion windows and closure assumptions;
- ideally an independently timed video/thermal passage reference that counts focal-camera **misses**, with precise overlap and documented reference sensitivity;
- an independent geographic/protocol heldout with positive source/camera crossing, and source-pool constraints or a multi-region hierarchy justified **before** biological data opening.

If the first two channels are verified but there is no calibrated passage reference, report **only `rho`, `psi`, and `d=a*p` under the above assumptions**. Do not label `d` a pure camera detection parameter, or claim direct ecological availability independently of registration. The separate preexisting three-CSV [reference-passage and exact-exposure validator](INDEPENDENT_REFERENCE_PASSAGE_AND_ECOLOGY_PROTOCOL.md) remains the route for the missing detector anchor.

## Reproducibility

The source-free executable `scripts/prove_multiregion_pool_identification.py` enumerates all 16 binary histories and exact Jacobian ranks, stores a deterministic machine-readable certificate at `docs/replication/MULTIREGION_POOL_IDENTIFICATION_RESULT.json`, and is tested in `tests/test_multiregion_pool_identification.py`. No random sampling, source download, workflow-based biology, model fit, photos or animal records are used.

## Prior methodological literature

These ideas build upon (not replace) established work on multiscale occupancy, imperfect detection and temporary availability:

- MacKenzie, Nichols, Seamans & Gutiérrez (2009), *Modeling species occurrence dynamics with multiple states and imperfect detection*, [DOI 10.1890/08-0141.1](https://doi.org/10.1890/08-0141.1).
- Multi-scale occupancy estimation using multiple detection methods, [DOI 10.1111/j.1365-2664.2008.01509.x](https://doi.org/10.1111/j.1365-2664.2008.01509.x).
- *Ignoring species availability biases occupancy estimates in single-scale occupancy models*, [DOI 10.1111/2041-210X.13881](https://doi.org/10.1111/2041-210X.13881).
- *Guidelines for estimating occupancy from autocorrelated camera trap detections* (2024), [DOI 10.1111/2041-210X.14359](https://doi.org/10.1111/2041-210X.14359).
