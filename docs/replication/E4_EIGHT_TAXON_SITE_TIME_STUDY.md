# E4: community-wide species-relative diel reordering with site–time controls

**Exploratory analysis specification — 2026-10-19, before opening the new site×season and site×year-month results.** The original eight-taxon E4 outcome, seven downward versus one upward marginal diel shifts, and the 8.706× site-adjusted rat/muskrat contrast were **already known**. This is explicitly outcome-informed, not independent discovery, E5 qualification, or confirmation. The exact eight-taxon roster, 28 unordered pair universe, stratification and stop rules are fixed here. No threshold change after results.

## Central ecology question

**Does a community's observed day/night assemblage re-sort between survey contexts after controlling for both physical camera location and season?** This differs from asking whether a single species has a nonstationary diel response. Species-specific relative changes may be informative even when the entire camera network shares an unknown observation process, but do not identify species' actual behavioral rhythms without external detection calibration.

Previously frozen findings establish that the camera-record night/day ratio generally fell between annotated training and east-heldout D for **7 of 8** eligible taxa, while *Rattus norvegicus* increased. The rodent pair had a pooled relative odds ratio-of-ratios of **9.59837** and a physical-site Mantel–Haenszel version of **8.70607** at 20 west and 8 D informative physical locations. The new test must ask if that apparent reversal is merely a **season mixture** and if the community-wide pair patterns extend beyond these two selected rodents.

## Source and transparent post-outcome boundary

- Frozen independent of this script: MICA capture [run 36369531079](https://github.com/zuizui0223/esdm/actions/runs/36369531079); exact archive SHA256 `8346f3fe467a201525d6bedd4ebd6e2078457ee8bb778501d41d55ace7d962c9`.
- Same 266 annotated-training and 164 east-heldout D deployments as the eight-taxon E4 receipt, and the same quarantined anomalous event IDs.
- Exactly eight previously eligible taxa: *Anas platyrhynchos*, *Ardea cinerea*, *Capreolus capreolus*, *Fulica atra*, *Gallinula chloropus*, *Ondatra zibethicus*, *Rattus norvegicus*, and *Vulpes vulpes*.
- Units: unique `deploymentID + eventID + scientificName` records, same local `eventStart` six-hour day/night definition; no new taxonomy, threshold or opportunistic taxon screening.
- Two **pre-specified** physical-site temporal controls: (1) site × meteorological-style calendar season (DJF/MAM/JJA/SON; pooled across years), (2) the more restrictive site × calendar year-month. The second is a precision/coverage sensitivity, not a switchable winning endpoint.

Within each site × time bin, a species pair (`i`, `j`) supplies the 2×2 event table `a=night_i, b=day_i, c=night_j, d=day_j`. A valid cell needs positive species totals and positive day/night totals. Its conditional comparison is the observed species-relative diel odds `(a/b)/(c/d)` if defined. Across informative cells, a *descriptive*, exposure-common Mantel–Haenszel ratio is `Σ(ad/n)/Σ(bc/n)`. A physical-site/time-bin shared multiplicative detection or exposure factor cancels from a *single cell's* true species-relative odds, assuming the same observation effect for both taxa. But changes in strata weighting can alter the Mantel–Haenszel average under heterogeneous effects, and no species-specific camera sensitivity was measured.

## Frozen rules and complete-result reporting

For every one of the **28** fixed unordered taxon pairs:

1. Require **≥3 distinct physical camera sites**, **≥4 informative site×time-bin cells** and **≥2 distinct time bins** within *each* cohort, plus positive numerator and denominator MH crossproducts.
2. Report all 28 pairs whether or not the requirements are met. If either cohort lacks support, return `PAIR_NOT_COMPARABLE`, never an imputed infinite odds or 0.5 pseudocount.
3. For estimable pairs report the separately site×time-adjusted species-relative night/day odds in training and D, their domain ratio, and whether this crosses one (pairwise rank reversal).
4. Compute leave-one-physical-site-out ranges only where at least four supporting sites permit remaining ≥3 sites and the other fixed minima. A reversal is described as stable only if **both** LOO ranges are calculable and wholly on opposite sides of one.
5. Summarize the count of comparable pairs, observed rank reversals, and stable reversals. **Do not** select the most attractive pairs as an independent test, claim pairwise network ordering is transitive, infer a camera-independent abundance signal, or calculate event-level confidence intervals.
6. Report the fixed *rat/muskrat* pair separately (without picking a new favorite) for direct comparison with earlier site-only 8.706× estimate.

Site grouping reduces some location/season composition bias but **does not** match the *same* physical locations between east and west, nor establish common camera detection across species. Event-count autocorrelation, differences in site microhabitat, observation source, taxa and seasons can all remain. No causal inference, competitive niche partitioning, cross-taxon universal law, or E5 G4 pass follows from a positive result.

## Terminal interpretation logic

- **If** a multi-pair site×season set is estimable, the claim is merely a positive observed community-relative temporal reordering across these camera contexts, with its fixed list of support-limited pairs.
- **If** the finer year-month analysis agrees for some pairs, seasonal mixture alone is less convincing as a complete accounting explanation for those *observed records*, but detection and geography/source confounding remain.
- **If** data support is insufficient, write that refusal; do not relax site, temporal-bin, or pair requirements or rescue the outcome by pooling more time.
- A later independent dataset must couple year-round shared-site physical replication to passage-reference/taxon-specific camera calibration and crossed geographic/source design before inferring true temporal niche mechanisms.

Related existing results: [frozen E4 cross-taxon receipt](E4_MICA_POSTRESULT_CROSS_TAXON_DIEL_SUPPLEMENT.json), [rodent shared-camera-site audit](E4_COMMUNITY_RELATIVE_DIEL_RESULT_RECEIPT.json), and [E4–E5 evidence limits](E4_E5_ECOLOGICAL_EVIDENCE_SYNTHESIS.md). This independent analysis has **no new biological result at the time of freezing these fixed rules**.


---

## Completed independent site–time diagnostic (post-outcome, 2026-10-19)

The already-specified audit [GitHub Actions run 39208596309](https://github.com/zuizui0223/esdm/actions/runs/39208596309) succeeded after **7 synthetic contract tests passed**, using the SHA256-pinned original MICA archive and the original eight-taxon event counts. It introduced no model fit and exported no event-level rows or camera names. Original aggregate result ZIP: artifact **12167010654**, SHA256 `bbbdf19749f1551f5105f8d4ae7cbddb68cc88dd3e08f65ae0dc65f921190748`. See the [frozen result receipt](E4_EIGHT_TAXON_SITE_TIME_RESULT_RECEIPT.json) and the [complete fixed 56-row output](E4_EIGHT_TAXON_SITE_TIME_ALL_PAIRS.csv), which includes nonestimable pairs rather than selectively omitting them.

| Full eight-taxon fixed-pair comparison | Site × season | Site × calendar year-month |
|---|---:|---:|
| Possible pairs | 28 | 28 |
| Data-qualified pair contrasts | **15/28** | **12/28** |
| Pairs crossing species-relative recorded diel odds = 1 | **5** | **3** |
| Reversals with fully separated leave-one-physical-site-out ranges | **2** | **1** |
| Unestimable pair contrasts | **13** | **16** |

### Fixed rodent pair: reversal retained under both temporal controls

For `Rattus norvegicus` **relative to** `Ondatra zibethicus`:

| Descriptive site-time-adjusted measure | Annotated training | Heldout D | Cross-domain ratio |
|---|---:|---:|---:|
| Rat/muskrat odds, site × season | **0.67033** (16 sites) | **4.51466** (8 sites) | **6.73495×** |
| Rat/muskrat odds, site × year-month | **0.65377** (14 sites) | **6.35765** (8 sites) | **9.72464×** |

Both reversals survive deletion of any individual informative physical site **within each cohort**. These are not two independent replications: they reuse the same observed E4 network with distinct time-stratum definitions and different subsets of informative sites. Their changes from the earlier 8.706× site-only ratio should **not** be construed as effect-size improvements produced by the adjustment.

**Substantive ecological-pattern finding:** the relative *recorded* night/day timing of these two rodents changes across the observed camera-network regimes even after controlling for whether the two species share a physical camera location and a calendar season, or the same site/year-month. Consequently unequal seasonal mixtures and disjoint recorded physical camera locations alone are insufficient explanations *within these summaries*. This does **not** exclude taxon-specific sensor detection, within-camera microhabitat-use differences, site-heterogeneous weighting, or geographic/source protocol confounding.

### Second inversion: two waterbirds, weaker temporal robustness

The `Fulica atra` / `Gallinula chloropus` recorded-diel pair reverses under site×season control: **1.38066 → 0.77188** (20 vs 7 informative sites). Both ranges from leave-one-site deletion stay on opposite sides of one (training **1.25406–1.64405**; D **0.71609–0.85552**).

Under finer site×year-month control, the descriptive point estimates remain on opposite sides of one (**1.26919 → 0.86640**, 17 vs 5 informative sites), but **the D leave-one-site-out interval-like sensitivity range crosses one** (0.81113–1.20090). Thus this pair is **not** robust at the finer time resolution; do not collapse the 2 season-level reversals into 2 reliable monthly reversals.

The other 3 season-level and 2 month-level reversals did not satisfy the declared leave-one-site robustness criterion; all are shown in the pair matrix. These are descriptive post-selection contrasts, not statistically controlled multiple comparisons.

### Meaning and next scientific step

The new positive empirical insight is **heterogeneous relative daily observation profiles within a recorded multispecies assemblage**, not merely the failure of a muskrat predictive activity term. A taxon-common within-site/time detection factor would cancel from an individual 2×2 species-relative odds, but **that common-factor assumption is untested**, and the Mantel–Haenszel mean itself can change through site weighting in heterogeneous contexts. We cannot claim actual species behavioral niche movement, competition, a general law of animal communities, or a second geographically independent validation. Original E4 and E5 status stays unchanged (E5 0/17 standard-qualified).

A test of **true ecological temporal partitioning** should collect independent known-passage/video denominators or matched taxon-specific sensor calibration at simultaneous year-round multispecies sites, use crossed geography/sensor source, and prespecify community-relative and taxon-specific diel contrasts. In independent data, the *observable claim* to examine prospectively is whether the same rodent relative timing shift appears after controlling for site and month; the *causal mechanism* requires new calibration.
