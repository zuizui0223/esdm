# Safari14: recorded mammal replacement exceeds a null preserving camera richness AND taxon camera incidence

**Completed 2026-11-14.** This is a **new, explicitly post-result camera-level conditional-randomization sensitivity** to the original independently observed Safari14 protected-area mammal community analysis. The original observed positive median turnover dominance was known; this is neither a confirmatory ecological test nor a correction to the earlier frozen Safari14 result. All values are sourced from the [successful GitHub Actions audit 43580142370](https://github.com/zuizui0223/esdm/actions/runs/43580142370), with original and new source hashes recorded in the [immutable evidence receipt](SAFARI14_FIXED_MARGINS_NULL_RESULT_RECEIPT.json).

## What changed from the earlier illustrative null

The [original Safari14 spatial field result](SAFARI14_SPATIAL_BETA_ECOLOGICAL_SYNTHESIS.md) detected higher **Simpson species-replacement β_sim** than nestedness-resultant β_sne in both the original seven-park discovery and five-park validation partitions after drawing the same 10 physical cameras per park 500 times. The [first retrospective null](SAFARI14_STRUCTURAL_NULL_ECOLOGICAL_INTERPRETATION.md) showed that **the mere condition β_sim > β_sne can also arise in 500/500 random park species-list assignments**, preserving only park species-count medians. That study was a valid falsification of an *overstrong interpretation*, but it could not test whether observed reserve assemblages were more differentiated than allowed by the original camera-level prevalence of species.

The new test reconstructs the **actual eligible camera×mammal-label binary incidence matrix** from the original source (no wildlife image downloads), conditioned on all the original frozen camera-selection and taxonomic rules. The source ZIP SHA256 was exactly `2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1`. Importantly, it **reproduced the previously archived 500/500 original draws, all reported median Sørensen/Simpson/nestedness statistics and eligible 91 park-pair support before making any null comparison**, and the original full per-source QC was identical. The source result JSON SHA256 was `f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7`.

## Frozen conditional null and result

In each of the original partitions separately, the **curveball** algorithm reallocated observed wild mammal labels between eligible physical camera rows, strictly preserving:

- **Each eligible camera's number of distinct detected mammal labels** (camera-row degree);
- **Each mammal label's total number of eligible positive cameras within the whole partition** (taxon-column degree);
- Camera and park membership and station numbers, exact original 10-camera sampling selections, original ≥2-positive-camera taxon threshold, and the original 7/5 park split.

The randomization **does not** preserve particular mammal species' association with a specific park: *that affiliation is the response of interest*, tested against the null assumption that camera species labels could be exchanged across parks inside the fixed source partition. The global 38 original mammal labels include two that had no eligible-camera records in some partitions; each eligible partition actually had **36 positive camera-detected labels**. There were **696** discovery cameras with **4,915** camera×species positives and **410** validation cameras with **3,508** positives.

Two fixed nonadjusted randomization chains (seed 20261114/20261115) used 30 proposals per camera for burn-in and 15 per camera between 500 paired simulated matrices. Exact camera and taxon margins were checked throughout, not approximately adjusted. The primary statistic is **within-draw park-pair-median observed β_sim minus its null β_sim using the *same* preselected 10-camera-per-park sample**. The median of paired differences is *not* necessarily the difference of separately reported medians.

### Main empirical/null comparison

| Fixed group of reserves | Original observed β_sim median | Row+column-margins null β_sim median | Median of paired observed-minus-null β_sim differences | Paired draws observed > null | Null draws with β_sim > β_sne |
|---|---:|---:|---:|---:|---:|
| Discovery **7 parks**, 21 pairs | **0.4444** | **0.0833** | **+0.3889** | **500/500** | **18/500** |
| Validation **5 parks**, 10 pairs | **0.3556** | **0.1181** | **+0.2396** | **500/500** | **354/500** |

All **500** paired draws in both partitions retained complete park-pair support. The observed-minus-null pair-draw differences had descriptive 5–95% ranges of **0.275–0.500** in discovery and **0.132–0.330** in validation. These ranges are **NOT confidence intervals**, and 500/500 is **NOT a formal permutation P-value** (randomization states arise from one serial MCMC-like trade chain per partition; mixing and uniform sampling have not been independently proved, and draws reuse the same camera networks).

The original fixed rule was positive in both partitions: **at least 475 of 500 valid paired draws must have observed β_sim > fixed-margins-null β_sim**; here the count was **500 in each**. This is stronger than the original descriptive observation alone and distinct from the first, richness-only artificial null.

### Reserve-level heterogeneity, including negative evidence

All **31** eligible within-partition reserve-pair comparisons (21 discovery, 10 validation) are included in the original full [13,174-byte result JSON](https://github.com/zuizui0223/esdm/actions/runs/43580142370/artifacts/14107094556), as are per-partition traded-margin integrity totals and null medians.

- **Discovery**: 19/21 individual park pairs had higher median observed β_sim than the null, but **2/21 did not**. \`CDB–KAR\` had observed β_sim 0.125 versus null 0.1667; \`APN–KRU\` had 0.0714 versus null 0.100. Thus the partition-level pattern is not universally true for every protected-area contrast.
- **Validation**: all **10/10** eligible park pairs had higher median observed β_sim than the fixed-margins null. However, those comparisons share species, cameras and environmental context and are **not independent sample replicates**.

The randomizations accepted 4,778,313 trades between discovery replicates and 2,869,714 trades between validation replicates, with exact camera and species occurrence margins intact. This verifies extensive relabeling activity but **does not prove stationarity or uniform sampling of all possible fixed-margin matrices**.

## Ecological meaning and limitations

**Supported:** mammal label combinations **recorded at physical camera sites are more associated with particular reserves** than expected under a **within-partition, exchangeable-camera assignment that fixes both observed camera richness and taxon camera prevalence**. That is a positive *conditional incidence* result beyond the simple mathematical β_sim > β_sne headline. It appears in both predeclared, geographically distinct groups of reserves, although they share the LILA/Snapshot Safari source programme. In practical ecology it suggests that reserve mammal *record profiles* are not simply globally shuffled combinations of the same species.

**Not supported:** a universal reserve-level exception-free pattern, nonrandom **biological** community assembly against an environmentally or biogeographically realistic species-pool null, causal dispersal isolation, environmental filtering, habitat partitioning, direct interspecific competition, actual regional presence/absence, detection-corrected occupancy or abundance. The exact conditional null assumes cameras across different parks in each group are exchangeable. Real parks have distinct geographic source pools, accessibility, camera traps, vegetation, detection probability and unmeasured operating effort; any of those could explain the observed excess. A camera's count of observed species **is not** proof of equal sampling effort or a detection probability.

Neither the 500 repeated camera draws nor the serial curveball matrices are 500 independent ecological populations. It is scientifically inappropriate to convert the counts into a P-value, uncertainty interval or calibrated SDM predictive score. The result is **one conditional sensitivity on the known original source**, not a new independently collected wildlife dataset. The original temporal-field data E7/E7-C results and E4/eSDM fit are unchanged; original E5 **0/17 qualified and G4 unpassed**.

## Recommended next *different* scientific test

The meaningful next step, rather than more arbitrary random-set models, is independent camera operating-day logs and reference detection (or identifiable occupancy repeat visits), measured park habitat/biome/geography and a **prospectively declared source-region constrained species pool**. This would ask whether unexpected park differentiation remains **after respecting which mammals can actually reach and be detected in each reserve**. Randomizing across ecologically impossible park/species combinations can systematically exaggerate an observed signal. Do not use the current positive outcome to tune a new null until it passes an unopened independent reserve network.

## Reproducibility

- [Frozen **before S14-FM source opening**](SAFARI14_FIXED_MARGINS_NULL_FROZEN_DESIGN.md).
- [Successful exact-source S14-FM workflow](https://github.com/zuizui0223/esdm/actions/runs/43580142370), 6 synthetic correctness tests passed and original 500 camera draws reproduced.
- [Full per-park-pair, margin audits and 500-draw summary artifact](https://github.com/zuizui0223/esdm/actions/runs/43580142370/artifacts/14107094556); ZIP SHA256 `a9f32536b4120c249abd57c59981e6cfcaab4deb19016b788a0000ac35bd06dc`, inner JSON SHA256 `4dcf8212510524dccefbfa250e05277fe55085f3b838c33a1c5f7fc8ee593b5e`.
- [Short machine-readable result and claim firewall](SAFARI14_FIXED_MARGINS_NULL_RESULT_RECEIPT.json).
- [Original non-null camera equalization result](SAFARI14_SPATIAL_BETA_FROZEN_RESULT_RECEIPT.json) and [earlier weak-null falsification](SAFARI14_STRUCTURAL_NULL_RESULT_RECEIPT.json).
