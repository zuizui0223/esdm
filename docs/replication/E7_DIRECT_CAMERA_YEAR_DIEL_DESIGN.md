# E7-C: Direct same-camera/year species-diel contrasts, without pooled MH weighting

**New endpoint, post-result exploratory design — fixed 2026-10-28 before inspecting E7-C within-cell outcomes.** The previous E7 whole-survey response, 66-pair pooled MH effects, 23/46 direction concordance, and the noncollapsibility counterexample are **already exposed**. E7-C is explicitly a new descriptive estimand on the **same** Snapshot Serengeti source records, not an independent confirmation, E7 original retry, E8 model generation, or E5 detection-calibration rescue.

## Problem and falsifiable comparison

The earlier E7 pairwise Mantel–Haenszel summary differs among species pairs in both camera/year support and pair-specific weights. Synthetic data show that even a shared set of camera sites can generate non-zero pair-triangle gaps **with no species' within-site night/midday ratio changing**. To test whether any **observed** species-relative seasonal changes remain when eliminating this particular aggregation issue, the new unit is a **single camera location × hydrological year**, shared by all taxa compared within that unit.

Use the **original frozen 12-category discovery roster** (zebra, wildebeest, hyenaSpotted, gazelleThomsons, warthog, gazelleGrants, giraffe, elephant, hartebeest, buffalo, lion, reedbuck), and all **66 unordered pairs**. No new species selection, exposure filters, season definition or thresholds based on the outcome. Discovery source seasons **S01–S05** and validation **S06–S11** remain separate; sites may recur across source seasons. As in E7, core wet = **Nov–Apr**, dry = **Jun–Sep**; night = **21:00–03:59**, midday = **10:00–15:59**. Original camera clock timestamps, taxon whitelist and `seq_id` deduplication are unchanged.

For species `i` at site-year `s`, let `N_{i,s,W}, D_{i,s,W}, N_{i,s,R}, D_{i,s,R}` be the **recorded unique-sequence counts** in night/midday, wet/dry. A species contributes an exact finite local seasonal diel contrast only if **all four** counts are strictly positive:

`d_{i,s} = log(N_{i,s,R}/D_{i,s,R}) − log(N_{i,s,W}/D_{i,s,W}).`

For species pair `i,j`, both taxa must qualify at exactly the same site-year, and the local relative contrast is `d_{ij,s} = d_{i,s} − d_{j,s}`. This avoids pair-specific MH weights **at the local level**. It is not a species-independent observation estimate and does not recover individual animal activities.

### Frozen minimum support and summary

For each pair, within each source-season partition:
1. Count all exact locally eligible same-camera/year comparisons. Require **at least 10 matched site-years**, **5 distinct physical camera names**, and **3 distinct original source-season ZIPs** represented in the union of eligible site-year wet/dry records.
2. If these are unmet, return `INSUFFICIENT_DIRECT_CELL_SUPPORT` without continuity corrections, new pooling, changing time bins, or dropping unfavorable pairs. Return all 66 pairs (including refusals).
3. For supported pairs, the **primary score** is the **equal-site-year median** of `d_{ij,s}`, with a separately reported unweighted mean and descriptive fraction of site-years where `d_{ij,s}>0`. The median is robust to very large event-count imbalance but does not guarantee statistical independence of repeated physical sites; no p-value/CI.
4. Recompute the median dropping **one physical camera name at a time**. Describe sign-robustness only if *all* such deletions still meet the original support and have an unchanged nonzero sign.
5. For supported pairs across *both* source partitions, compare median signs, calculate the sign agreement count, and report the number of exactly sign-robust transfers; do not modify original E7 primary outcome.
6. Report complete-site-year triple support for *all* `12 choose 3 = 220` taxon triples. At the same site-year where all three species have four strictly positive cells, `d_ij,s + d_jk,s − d_ik,s = 0` must hold **exactly up to numerical precision**; report number of such triple-site-year checks and maximum residual. This identity is **tautological** for one common within-cell definition and **not evidence for or against interactions**.

## Comparability and ecological inference

This is an explicitly **post-outcome** direct-cell question. The strict positivity gate can discard many sparsely observed taxa, especially highly diurnal/nocturnal ones. A zero/negative or underpowered outcome is a valid terminal result; there is **no threshold rescue**. Discovery and validation reuse the same source program, sometimes locations, so this is not independently transported to another biome.

A common night/midday effort/detection factor shared across species in one site-year/phase cancels from species-relative odds, but that assumption was **not established**. Species-specific camera detection, vegetation, group size, visit rates, shifts in migration, observation effort and seasonal geography can still produce apparent diel changes. There is no independent weather or NDVI series linked to these camera-years yet: do **not** infer measured rainfall, resource change or causal vegetation effects from calendar season.

The decisive question is narrower: **Does any observed seasonal species-pair signal survive the elimination of pair-specific MH aggregation and exact same-camera/year support?** If it does, it is a well-defined camera-record pattern and a stronger target for new independent calibrated field evidence. If it does not, the earlier pooled claims are composition-sensitive.

## Immutable source and execution firewall

Use the 11 original public Snapshot Serengeti metadata ZIPs whose SHA256 digests were pinned in `docs/replication/E7_SERENGETI_SOURCE_FORMAT_STOP.json`. The only permitted new biological access is a **separate, expressly titled E7-C exploratory audit**, not a rerun of E7's original primary pair-MH endpoint. The script calls the already-verified E7 source parser to reuse the same event deduplication and freeze the 11 per-season QC counts against the original empirical receipt's totals; all per-site and per-sequence keys remain internal. A new GitHub Actions execution must upload **only aggregated pair summaries, support counts, source hashes and an explicit terminal decision**, not raw camera IDs, sequence records or the whole source ZIPs.

**Pre-output assertions:** all 11 original archive SHA256 digests, the exact 12-category panel and earlier E7 source QC. **No** new NumPyro/SPDE model, posterior fit, E4 re-run, E5 G4 qualification, taxon-screening adaptation, event-level statistical confidence interval or environmental causal claim. Original E4, E5 and E7 frozen outcomes remain unchanged.
