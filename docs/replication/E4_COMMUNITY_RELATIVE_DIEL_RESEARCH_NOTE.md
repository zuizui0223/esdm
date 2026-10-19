# E4 community-relative diel structure — rat vs muskrat (post-outcome)

**Research note (2026-10-19).** A genuinely *ecological* question is whether the **relative temporal composition of a camera-recorded community** changes non-uniformly between the frozen E4 annotated-training and eastern D-prefixed observation networks. This does **not** assert a new causal observation correction or true behavioral niche inversion.

**Selection transparency:** This rat–muskrat contrast was identified *after* reading the already-frozen 8-taxon exploratory result. It is an **outcome-selected follow-on hypothesis and descriptive test**, not a preregistered, statistically independent discovery. The focal E4 muskrat response has already been used in E4; none of these observations qualify as new E5 independent evidence.

## New quantitative descriptive observation from the frozen cross-taxon receipt

The existing E4 cross-taxon receipt uses unique animal-level `deploymentID + eventID + scientificName` keys with the frozen temporal quarantine. Night is 18:00–05:59 and day is 06:00–17:59 using the existing local `eventStart` field.

| Cohort and taxon | Night events | Day events |
|---|---:|---:|
| Annotated-training — `Rattus norvegicus` | 4,348 | 463 |
| Annotated-training — `Ondatra zibethicus` | 1,237 | 100 |
| Eastern heldout D — `Rattus norvegicus` | 1,694 | 78 |
| Eastern heldout D — `Ondatra zibethicus` | 3,812 | 1,279 |

The relative **detected** night/day odds, rat divided by muskrat, are

`OR_train = (4348/463)/(1237/100) = 0.75916966`

`OR_D = (1694/78)/(3812/1279) = 7.28679339`

`OR_D / OR_train = 9.59837274` (log shift `+2.26159358`).

Thus a **rank-order reversal in the observed aggregate community relative diel profile** is present in the fixed archived result: rat records are relatively less nocturnally skewed than muskrat in annotated training, and relatively more nocturnally skewed in heldout D. Six of the seven other eligible nonfocal taxa have negative diel ratio shifts (rat is the only positive case among all eight). These are observed record patterns, not estimates of underlying passage timing.

## Why this is not only the preceding detection-failure story

At the *same physical location* `s`, with a hypothetical taxon-common multiplicative observation factor `q_s,t` and same effort `E_s,t`,

`Y_i,s,t = E_s,t * A_i,s,t * q_s,t`

then the relative diel count odds

`OR_s = (Y_R,s,N/Y_R,s,D) / (Y_O,s,N/Y_O,s,D)`

cancel both `E` and the shared `q` exactly. A change in one **taxon-common night/day detector multiplier alone** cannot explain a species-relative change at a matched camera site. This cancellation is an **algebraic conditional result**, not evidence that detection *really is* common to rat and muskrat. Different body sizes, gait, camera approach, microhabitats or taxon-specific detection, as well as unshared location/season composition, can all change the recorded species ratio.

The strong *pooled* contrast does **not** establish the same-site pattern; the species may be recorded at different sites. This is why a next diagnostic is needed.

## One separately labeled, finite field-data diagnostic

The companion script reads the already-pinned E2 MICA archive and frozen quarantine without fitting any model. Its fixed target is **one physical `locationName`** within each original observation stratum. It counts unique events for the two fixed species and time bins, then reports:

1. The number of independent named camera locations per cohort, including locations with **both species**;
2. How many locations contain **both species and both time bins** (i.e., contribute a potentially informative 2×2 table);
3. A **descriptive Mantel–Haenszel site-stratified rat/muskrat night/day odds ratio** only if at least **3** informative locations and both pooled cross-products are positive in *each* cohort;
4. A descriptive ratio of the two site-stratified odds and leave-one-informative-location-out range where separately computable.

The minimum site support and the two target species are fixed before this site-level output is inspected. If either cohort is insufficient, the terminal status is `SITE_MATCHED_TRANSFER_NOT_ESTIMABLE_WITH_FROZEN_SUPPORT`. **No threshold reduction, endpoint selection, new estimator or rerun** is licensed by a failure. The site-stratified contrasts do not create paired longitudinal geographic sites: the two cohorts contain different physical locations and a confounded source/geography shift.

Counts are never output with individual location names; only aggregate site-support and summary contrasts leave the isolated action. An event-level confidence interval would pseudo-replicate within-location and temporal autocorrelation, so **no new inferential p value or confidence interval is calculated**.

## What could become a testable biological hypothesis

**H — Community-relative diel reorganization:** Across standardized deployments, different mammal species show different diel responses to environmental and anthropogenic context rather than changing together along a common day/night gradient. Testing **true passage niches** requires co-observed passage references or independent, taxon-specific detection calibration at overlapping sites, with season and habitat/camera placement accounted for.

This contrasts with the narrower claim that a fixed marginal detector correction failed. Work on camera-trap placement has already demonstrated systematic distortion of inferred diel activity ([Scientific Reports 2021](https://doi.org/10.1038/s41598-021-02459-w)); camera-trap studies also document variation in the relative timing of sympatric mammal species ([PLOS ONE 2016](https://doi.org/10.1371/journal.pone.0163602)). The **new E4 contribution**, if supported within sites, would only be an *exploratory* example of differential recorded-community changes under the frozen west/D survey contrast, not a novel universal ecological law or evidence of competition.

**Historical results left untouched:** E4 activity gain −0.639051 and state gain +0.008391; E5 original G4 remains unpassed (0/17 qualified); Wolfson UNRESOLVED/HOLD, Rhode Island nonidentification, and Findlay descriptive-only stage results. This is **not** an E4 rescue, E5 replication, or attempt to recover activity/detection separately from the original survey.

## Source lineage

- [Frozen eight-taxon receipt](E4_MICA_POSTRESULT_CROSS_TAXON_DIEL_SUPPLEMENT.json)
- [Frozen E4 scientific synthesis](E4_MICA_POSTRESULT_SYNTHESIS.json)
- [Prior E4/E5 evidence limits](E4_E5_ECOLOGICAL_EVIDENCE_SYNTHESIS.md)
- [Source and site-level audit script](../../scripts/audit_e4_community_relative_diel.py)

**Site-level audit result:** not yet opened as of this note. Its one-time GitHub Actions artifact is the next finite, inspectable empirical step.
