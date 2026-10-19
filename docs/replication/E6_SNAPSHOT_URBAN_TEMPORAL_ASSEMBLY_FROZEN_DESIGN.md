# E6 independent macroecological test: urban development and temporal assemblage reordering

**Design freeze 2026-10-19 — BEFORE opening SNAPSHOT USA sequence outcomes.**

This is a new ecological programme, **not a rescue or qualification of E5**. The hypothesis was motivated by the previously exposed MICA E4 8-taxon result, but neither MICA events nor prior species-effect directions are used for the E6 primary empirical estimates. Taxa and quantitative contrasts for SNAPSHOT USA are selected and computed by the deterministic rules below rather than by favorable outcomes.

## Central question and falsifiable predictions

**Does human development reorganize *species-relative daily camera-record rhythms* within a mammal assemblage, rather than producing a single shared shift toward nocturnal recording?**

H1 (primary ecological observation): relative deep-night-to-midday odds for co-recorded mammal species differ between low-development (wild + rural) and high-development (suburban + urban) camera arrays. At a given physical deployment/site/time cell, a hypothetical taxon-common detection multiplier cancels in the *species-relative* night/day odds, whereas a true species-differential change, or species-differential sensor detection, does not.

H2 (temporal transport): development-associated pairwise direction estimates from 2019–2023 recur in **2024**, a prospectively separated temporal observation dataset. Concordance across years is the key generalization check; we will report all comparable pairs, not just successes.

H3 (geographic sensitivity): patterns are evaluated in a fixed 5-degree-latitude × 10-degree-longitude **shared-development support** subset, so that purely disjoint large geographic regions can be distinguished from comparisons within co-represented geographic cells. This is a *sensitivity*, not causal identification.

These hypotheses are **not** that competition is proved, urbanization causes behavior, all species respond identically, or camera detection is calibrated.

## Public independent datasets and exact file pins

Official repository: SNAPSHOT USA Dryad, under its published CC0 data license.

| Data partition | Published DOI | Dryad version | Sequence file SHA256 | Deployment file SHA256 |
|---|---|---:|---|---|
| 2019–2023 exploratory discovery | [10.5061/dryad.k0p2ngfhn](https://doi.org/10.5061/dryad.k0p2ngfhn) | 358059 | `8a442b130f11272c354de10ff97f69c65ae738a6514459f1431e963708011ded` | `9e837bba556de86af5934abcb5d8a487206df2b340a8b28fa8cc135c7bb7ec56` |
| 2024 **untouched-year test at freeze** | [10.5061/dryad.bnzs7h4qf](https://doi.org/10.5061/dryad.bnzs7h4qf) | 445070 | `252724a52bf656b2d1dda7d07018ccdc5ad571c0011eee33a05eccf12e005d2a` | `b742e8789fa18c83713f2dec76e342857c122c012ee464db5563f3b06d29970d` |

Dryad file IDs and original sizes (bytes), respectively: historical deployments `4016828 / 1,731,332`, historical sequences `4016829 / 206,672,092`, 2024 deployments `4788613 / 685,893`, 2024 sequences `4788614 / 72,884,138`. Download strictly from the Dryad API file IDs; hash-check **each** before parsing. Historical April 2025 **corrected** version is required, not the original version missing 2019 arrays.

This dataset is not a generic geographic replicate of MICA: it is US-based, has its own camera array and species identifications, and records mammal sequences and independently provided deployment metadata. SNAPSHOT USA's data-producer-provided `Development_Level` is an ordinal survey-array category, **not a randomized intervention or direct count of people**, and 2024 may reuse some of the older camera arrays. Thus holdout is independent **in observation year**, not automatically in arrays, project staff, or sensor hardware.

## Frozen data cleaning and sampling universe

- Select exactly September 1–October 31 of each sequence's recorded calendar year. This is the shared target survey season; August and November–December observations are excluded **for both partitions**. Do not add discarded months to rescue sample size.
- Use only animals with `Class = Mammalia` and a nonempty binomial `Genus + Species`. Unidentified animals and nonanimal trigger records do not contribute to pair ratios.
- **Exclude obvious humans/domestic pets/livestock** using a fixed pre-response list: `Homo sapiens`, `Felis catus`, `Canis familiaris`, `Bos taurus`, `Equus caballus`, `Ovis aries`, `Capra hircus`. No response-informed modification of the list. Wild/feral taxa not on the list remain eligible.
- Map each sequence to its deployment via exact `Deployment_ID`. Require a uniquely defined deployment metadata row; duplicate deployment IDs with conflicting site, array or development metadata are excluded, never arbitrarily joined.
- Unique event = (`Deployment_ID`, `Sequence_ID`, normalized `Genus`, normalized `Species`). Image/sequence duplicates never inflate counts.
- Physical site identity = (`Camera_Trap_Array`, `Site_Name`) within calendar year, with invalid blank names excluded. Unique camera **array** is the cluster/block for assessment and uncertainty; site-year sequence rows are **not independent spatial replicates**.
- Freeze a cross-latitude robust *deep-night* bin of local recorded clock hours `21:00–03:59` and *midday* `10:00–15:59`; omit all other hours (dawn/dusk). This does not recover exact astronomical sunrise/sunset and relies on recorder clock/timestamp validity; differing local clock protocols remain possible. No post-hoc hour-window change.
- Development group low = `wild` or `rural`, high = `suburban` or `urban`; missing or ambiguous categories are excluded. All four raw categories and exclusion totals will still be counted. No alternate development cutpoint after response reading.
- Latitude/longitude sensitivity bins of width **5 degrees latitude × 10 degrees longitude** from the metadata only, with exactly the same fixed grid and categories across periods.

## Frozen roster and estimand

**Roster selection using the 2019–2023 partition alone:** take **12 mammalian species** with the greatest number of unique (`Camera_Trap_Array`, year) combinations with at least one valid sequence in Sept–Oct, with deterministic ties resolved by the number of physical site-years and then lexicographic scientific name. This selection uses historical *presence frequency only*, not time-bin contrasts or development-effect directions. Freeze the resulting roster in the output *before* evaluating any 2024 outcomes. If fewer than 2 are available, fail closed. **No 2024 response can change the roster.**

For every unordered pair of the fixed 12-taxon panel (66 total), separately for historical and year-2024 partitions and low/high development groups, build 2×2 counts of night/midday sequence records from **the same named physical camera site-year**. A pair/site-year is informative only if both taxa recorded and both time bins represented (across species). Compute a descriptive site-stratified Mantel–Haenszel odds:
`OR_{ij,g} = Σ_s N_{i,s}D_{j,s}/n_s ÷ Σ_s D_{i,s}N_{j,s}/n_s`.

For a development effect, `L_ij = log(OR_{ij,high} / OR_{ij,low})`. The primary aggregate is the **complete 66-pair development shift vector** and whether the 2024 value has the same sign as the 2019–2023 value, among pairs estimable in both periods. Crossing odds=1 between low/high is a stricter *rank reversal* and reported separately. Aggregate concordance of 2024 vs historical is descriptive and does not automatically imply a significant population effect due to dependent species pairs.

### Strict finite support and robustness

For each development category in each temporal partition, require **≥5 distinct camera arrays**, **≥10 shared physical site-years**, **≥12 informative site-year 2×2 tables**, with positive aggregate MH numerator and denominator. If either development category fails, that species pair is `NOT_COMPARABLE`; do not use 0.5 pseudo-counts, pool pairs, lower threshold, or change roster.

Report the fixed paired species contrasts for every one of the **66 pairs**, including all refusals and reason/status, regardless of effect size. For comparisons passing these requirements, calculate leave-one-camera-array-out sensitivity (refusing if remaining support would fail) and the national descriptive relative odds. Spatial sensitivity retains only co-represented 5°×10° geographic grid cells containing **both** low and high development observations, require ≥2 such cells, then apply the same per-class support rules. **Do not decide which endpoint is primary after outcome.**

A positive independent-year result is a *directionally replicated observational pattern*, and never implies experimental urbanization causality or independently calibrated taxon-specific detectability.

## Result status, decision and stopping rule

1. Run a fixed header/file-integrity smoke test before downloading sequence contents. Hash and access failures are **transport stops**, not negative ecological findings.
2. Upon successful smoke test, execute **once** on the published corrected 2019–2023 data plus 2024 data using the exact frozen rules above. Record source blob SHA, run ID, schema, exclusions, fixed roster, all pair results, matched-grid sensitivity, original-sequence total, and explicit terminal status.
3. No response-based threshold tuning, rediscovery of favorable taxa, reruns of the same biological opening, post hoc choice of comparison geography, or unannounced model backend changes.
4. No p-values or uncertainty intervals from pretending sequences to be independent. The first release is an **honestly descriptive macroanalysis**. An inferential model would require a new preregistered external validation route and clustered sampling/variance treatment.

**Original E4 remains frozen and E5 qualification remains 0/17; E6 does not change either.**
