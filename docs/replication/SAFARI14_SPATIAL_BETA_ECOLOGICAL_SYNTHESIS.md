# S14 observed African mammal assemblage differentiation: replacement dominates nestedness

**Empirical one-shot:** [GitHub Actions run 42848095854](https://github.com/zuizui0223/esdm/actions/runs/42848095854), successful 2026-11-10 UTC. **Source-backed ecological synthesis:** 2026-11-12. This is the *new and separately frozen* **spatial** research question; the earlier [Safari14 diel PR #229](https://github.com/zuizui0223/esdm/pull/229) is a terminal timestamp-schema STOP, not a discovered or tested diel effect.

## Biological question and fixed scope

Within independently named African protected-area camera networks, are differences in the **recorded mammal species assemblage** driven primarily by species *replacement* rather than by the *nestedness-resultant* component associated with uneven detected richness? The initial hypothesis, 14 fixed park-code universe, 7 discovery and 7 validation split, original camera opportunity threshold, 10-camera equalization, 2-camera taxon presence threshold and 500 deterministic camera subsamples were locked [before wildlife labels were opened](SAFARI14_SPATIAL_BETA_FROZEN_DESIGN.md).

The study uses [LILA Snapshot Safari 2024 Expansion](https://lila.science/datasets/snapshot-safari-2024-expansion/) COCO metadata, not photos. Original source ZIP **SHA256 \`2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1\`**; 62,158,011 bytes. The Serengeti (\`SER\`) project is **excluded** because it overlapped the previously opened E7 Snapshot Serengeti source. Unknown project prefixes were also excluded rather than silently recoded.

The source contained **4,029,374 image metadata rows**. Within the **14 predeclared** non-SER project prefixes, there were **2,230,118 image rows**, **1,322,887 distinct recorded sequences** at **1,153 project×camera location keys**, and **594,868 recognized wild-mammal image annotation rows** across **38 whitelisted labels**. The last figure is annotation *rows*, including multi-frame sequences; the biological endpoint is **binary presence of any recognized label per physical camera**, not event counts, animal abundance, number of individuals or a true regional species census. No wildlife images, individual camera labels, sequence identities or coordinates leave the workflow.

## Real sampling support

The frozen 14 project universe was not silently changed. All **7 discovery parks** met the ≥10-camera condition, but only **5 of 7 validation codes** did: \`MLP\` and \`NIA\` had **zero camera metadata rows assigned to their original predeclared codes**. The study therefore has **12 usable projects**, not 14 completed projects. The fixed minimum of five validation projects was met. No alternate validation parks were substituted.

| Partition | Qualified projects | Qualified park pairs | Valid equal-camera draws |
|---|---:|---:|---:|
| Discovery | **7/7** | **21** | 500/500 |
| Validation | **5/7** | **10** | 500/500 |
| Cross-partition | 7 × 5 | **35** | 500/500 |

The full 14 choose 2 = **91** park pairs are preserved in the original artifact: **66** are eligible and **25** are nonestimable due to the two unsupported project codes. The 12 eligible parks have a combined **1,106** camera sites passing the ≥30 recorded-sequence proxy. Observed richness after rarefying to exactly 10 cameras per park varied markedly: median **6** wild mammal labels at \`LEC\`, **7** at \`KGA\`, **17** at \`APN\`, **19.5** at \`ENO\` and **20** at \`RUA\` (full per-project medians preserved in [receipt](SAFARI14_SPATIAL_BETA_FROZEN_RESULT_RECEIPT.json)).

## Primary ecological result

The preregistered camera-level resampling drew **10 physical cameras without replacement per eligible park**, 500 times, and only retained mammal labels found at **at least two distinct sampled cameras**. For each project pair, Baselga's pairwise decomposition calculated:

- Sørensen \`β_sor\`: total recorded assemblage dissimilarity;
- Simpson \`β_sim\`: species-replacement (turnover) component;
- \`β_sne = β_sor − β_sim\`: nestedness-resultant component.

For each draw, each partition used the **median over its eligible park pairs**. Values in the table are the subsequent median over the 500 draws; **medians are taken separately**, so \`median(β_sor)\` does not have to equal \`median(β_sim) + median(β_sne)\`.

| Fixed project-pair group | Median Sørensen dissimilarity | Median turnover β_sim | Median nestedness β_sne | Draws with median turnover > median nestedness |
|---|---:|---:|---:|---:|
| Discovery (21 park pairs) | **0.6429** | **0.4444** | **0.1257** | **500/500** |
| Validation (10 park pairs) | **0.4251** | **0.3556** | **0.0627** | **500/500** |
| Cross-partition (35 park pairs) | **0.5000** | **0.3333** | **0.1241** | **500/500** |

**The frozen primary criterion was met in both partitions:** the median recorded-mammal turnover component exceeded the median nestedness-resultant component for all 500 prespecified equal-camera selections; the prespecified requirement was ≥475/500 in each split. This is a positive, broad *observational* beta-diversity pattern, not an inferential p-value, confidence interval or proof that every park pair is turnover-dominated. The 500 camera draws reuse the *same underlying cameras and parks*; they are sampling-stability sensitivity checks, **not 500 independent field replicates**.

**Park-pair heterogeneity is substantial.** Among the park pairs already eligible in this one source, only **11/21** discovery and **6/10** validation pairs had turnover > nestedness in ≥95% of camera subsamples. Across partitions, **16/35** pairs met the same descriptive level, and **7/35** were turnover-dominant in fewer than half of subsamples. For instance, \`LEC\`–\`TSW\` had median \`β_sim = 0.1429\` versus \`β_sne = 0.3636\`, with turnover exceeding nestedness in only **20.6%** of draws. This illustrates why the **partition-level** general pattern must not be promoted to a universal statement about individual reserves.

## What this means ecologically

**Supported:** At the same fixed camera-station sample size, the mammal labels recorded in distinct protected-area networks often represent **different species combinations rather than simply species-poor subsets of richer reserves**. The pattern appears in the predeclared discovery and geographically distinct validation project partitions of this newly opened Safari source. In conservation terms it is compatible with the possibility that protecting distinct areas preserves **complementary detected assemblages**, but no conservation priority or optimal reserve network was tested here.

**Not supported:** a causal role of geographic isolation, temperature, precipitation, vegetation, anthropogenic disturbance, dispersal barriers or species interactions; exact ecosystem-level occupancy/absence, extinction or regional species richness; time-of-day effects (Safari source has no camera timestamps); taxon-specific camera detection or effort-corrected beta diversity; formal significance across independent replicate reserves.

Crucial biases remain: different camera models and placement, genuinely unknown camera operating days, taxa's unequal trigger probability, possible source project-alias issues (two original project codes unsupported), and a single provider for all reserve projects. The source 30-sequence threshold is **a proxy for recorded opportunity**, not an effort offset. The two geographic partitions are network-level internal validation within one dataset, not a new provider/calibration design.

### Current inference boundary and next decisive test

The result answers a scientifically interesting **macroecological assemblage-composition question** without adding another eSDM fitting generation. A stronger follow-up would independently cross-check project identities and use camera-active-day effort, park survey design, detection-corrected community occupancy or independent incidence replicates to see whether **true community replacement** remains dominant. Reserve-level environmental drivers require measured project covariates and a prespecified fresh heldout dataset, not post-result ecological storytelling.

The original E4 fitted model, E5 original **0/17 standard qualified and G4 unpassed**, E7 seasonal nontransport and E7-C strict-complete-cell support remain unchanged. This work is **not** a new claim of process-based eSDM predictive superiority.

## Source, artifact and reproducibility

- Full original **91-project-pair** and **14-park** machine-readable result: [GitHub Action artifact 13779138089](https://github.com/zuizui0223/esdm/actions/runs/42848095854/artifacts/13779138089), ZIP SHA256 \`320d14fd10a191330d74f2a41a40ea2ccf8f94dee911224e96e6e0ec90b7a582\`, inner \`SAFARI14_SPATIAL_BETA_RESULT.json\` SHA256 \`f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7\` (39,552 bytes).
- [Fixed before wildlife outcome](SAFARI14_SPATIAL_BETA_FROZEN_DESIGN.md).
- [Stable ecological evidence and full source/validity receipt](SAFARI14_SPATIAL_BETA_FROZEN_RESULT_RECEIPT.json).
- [Deterministic source parser and equal-camera resampling](../../scripts/safari14_spatial_beta.py) with 6 synthetic tests.


## Post-result audit of the *ecological interpretation* (2026-11-14)

A separate, **retrospective, aggregate-only structural null check**
was performed **without reopening any wildlife record**. With the original
twelve eligible parks' 10-camera median mammal-label richness preserved,
uniformly random assignment of the same 38 globally recorded labels also
produced partition-median **turnover > nestedness in 500/500 artificial
draws for both fixed reserve partitions**. Artificial global
image-frequency-weighted draws varied dramatically: the fully
image-count-weighted artificial pool yielded only 4/500 turnover-dominant
draws in the discovery parks versus 494/500 in validation.

These simulations are **not a field replication, an ecological null
hypothesis significance test, or frequency-preserving randomizations
of the real camera-by-species incidence matrix**. The frequency proxy is
image annotation rows (including burst frames), not true species presence
or independent animal passes. The mathematical result is nonetheless
decisive on one claim boundary: **the original positive observed
turnover-dominance criterion does not by itself demonstrate nonrandom
community assembly, dispersal limitations, climate filtering or
complementarity beyond a random baseline**. The original source, medians,
park and pair support, and original frozen primary result remain valid
and unchanged.

See [the full post-result null comparison](SAFARI14_STRUCTURAL_NULL_ECOLOGICAL_INTERPRETATION.md)
and [its pinned frozen aggregate receipt](SAFARI14_STRUCTURAL_NULL_RESULT_RECEIPT.json).
A future assembly-process claim needs park-by-species/camera incidence
margins, real effort, detection and biologically justified region-specific
species pools with an independently frozen response/validation design.
