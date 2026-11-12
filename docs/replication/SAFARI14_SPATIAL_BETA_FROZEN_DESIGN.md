# S14 spatial: continental African reserve assemblage turnover versus nestedness

**New independent *spatial* ecological endpoint, frozen 2026-11-11 BEFORE Safari2024 species annotations are opened.** This is a change of scientific question, NOT a repair or promotion of the [terminal timestamp-less Safari14 diel attempt](https://github.com/zuizui0223/esdm/pull/229). That attempt stopped on the original image metadata schema, with **zero clock-time contrasts computed**. The new study uses only field types actually present: camera location, image→sequence key and species annotation. **No datetimes are available or inferred.**

## Ecological question

Across broadly different African protected-area networks, is the spatial differentiation of **observed mammal assemblages** dominated by **species turnover** (replacement) or by **nestedness-resultant richness loss**? Does that distinction appear in two geographically disjoint sets of protected areas when **the number of monitored camera stations is equalized**?

**Not causal environmental filtering**: no project-specific annual climate, exposure duration, camera operating-day count or independently calibrated species detection is supplied. The claim is strictly **species observed in camera traps under a controlled equal-camera opportunity**, not underlying richness, true occupancy, trait distributions or a spatial SDM fit.

## Pinned data, independent of E7 Serengeti

[Official LILA Snapshot Safari 2024 Expansion](https://lila.science/datasets/snapshot-safari-2024-expansion/), metadata-only zipped COCO Camera Traps file:
`https://storage.googleapis.com/public-datasets-lila/snapshot-safari-2024-expansion/snapshot_safari_2024_metadata.zip`

The original 62,158,011-byte ZIP SHA256 is pinned as **`2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1`** from the prior *non-biological-image-schema* diagnostic, which never inspected the category response. Its public source covers ~4.03M image metadata entries, 1,824 named cameras across 15 protected-area projects. No image files are downloaded.

**SER (Serengeti) excluded** to avoid the previously opened E7 source. Prespecify 14 other project codes and retain their original LILA camera location strings internally. The same 7/7 project split originally pinned before any S14 response:

- Discovery: `APN, CDB, ENO, KAR, KGA, KRU, LEC`.
- Validation: `MAD, MLP, MTZ, NIA, PLN, RUA, TSW`.

Unknown project prefixes, source human/vehicle/empty classes and unresolved category labels are excluded with count receipts; **do not** reassign unknown projects by outcomes. Metadata timestamp absence is a fact, not a reason to estimate time bins from filenames.

## Frozen camera and mammal universe

- Per image source `file_name`, `location`, `seq_id` and `id`: map the original image ID to (`project`, `physical camera location`), and count each unique (`project, camera, seq_id`) exactly **once** for source-record *opportunities*. A repeated image in a multi-frame burst is not a new independent camera opportunity.
- Each camera has a set of mammal labels observed in ≥1 original annotation, regardless of repeated images; **binary incidence**, not image/animal abundance. Use a fixed wild African mammal-name whitelist, with source-independent lion sex/age pooling. Exclude unrecognized and domestic/nonmammalian categories without opportunistic reclassification.
- An **eligible camera** has at least **30 distinct sequence IDs** in the public metadata (including empty sequences), providing a *trigger/recorded-sequence opportunity proxy*, **not actual camera-on hours**. A camera meeting this threshold is not asserted to have equal detection probability or temporal duration with another site.
- A park must have **≥10 eligible cameras** for the primary spatial beta-diversity comparison. If fewer, it is reported as insufficient (no threshold relaxation).
- A taxon counts in the 10-camera subsample's detected assemblage only if recorded at **≥2 distinct sampled cameras**; this prespecified repeat-camera filter reduces single-camera noise but systematically excludes rare and poorly detected mammals. Every excluded category/camera still contributes to QA counts, not to species response.
- Both discovery and validation should have ≥**5 eligible projects**. If not, issue `INSUFFICIENT_DISCOVERY_VALIDATION_PARK_SUPPORT`, preserving the source/QC results without claiming a spatial biological effect.

## Primary statistic — rarefy cameras rather than animals/images

Use **500 deterministic independent-within-park** camera subsampling draws (Python PRNG `random.Random(20261111)`), each drawing exactly **10 eligible camera IDs without replacement per park**. The source camera incidence matrix remains fixed; these are **resampling sensitivities for camera opportunity**, not 500 independent biological replicates or inferential bootstrap CIs.

For each park and draw, define observed species set with ≥2 positive sampled cameras. For each pair of parks X,Y, let a be shared species, b unique X and c unique Y:

`beta_sor=(b+c)/(2a+b+c)`, `beta_sim=min(b,c)/(a+min(b,c))`,
`beta_sne=beta_sor-beta_sim`.

These are the pairwise Sørensen, Simpson turnover and nestedness-resultant components of Baselga (2010), [Global Ecology and Biogeography DOI](https://doi.org/10.1111/j.1466-8238.2009.00490.x). If either observed species set is empty, the comparison is explicitly missing, **not 1.0 dissimilarity by default**.

**Primary result:** for each fixed region partition independently, report median over **park pairs** of beta_sor, beta_sim and beta_sne in each camera draw, then the median across all 500 draws and descriptive fraction of draws where the project-pair median beta_sim exceeds beta_sne. Every one of 14 choose 2 = **91** project pairs is reported (even if a park failed eligibility); label discovery–discovery (21), validation–validation (21) and cross-partition (49). Do not select only high-dissimilarity pairs.

**Success criterion:** positive evidence for *observed cross-park species replacement dominating richness-related nestedness* requires **both** disjoint seven-park partitions to have median beta_sim > median beta_sne for at least **475 of 500** predefined camera subsamples, and each to include ≥5 eligible parks. This heuristic is a sensitivity decision, **not an ecological statistical significance level** because park pairs and camera resamples share units and do not estimate a superpopulation CI.

Secondary outputs: per-park camera count, number above the opportunity threshold, observed full eligible-camera species pool, equalized 10-camera species count median/range, and each project's overall inclusion/exclusion ledger; pairwise beta medians/ranges and turnover dominance fractions. Output **no raw per-camera IDs, image/sequence IDs, humans, image content or exact coordinates**.

## Bias, inference boundaries and termination

Camera-trap series count depends on triggering, station placement, sensor model, vegetation and search effort; a 30-sequence screen is **not a functional effort offset** and a 10-camera comparison does not control animal-specific detection. Different reserve biomes/geographies and animal movement vary, but no measured climate or biome cause is identified. Species sets are *observed labels*, not true regional absences or formally estimated occupancy. Therefore turnover/nestedness describe the *detected network* and may be exaggerated by sparse taxa/detection differences.

Report both positive and negative criteria exactly. Even if all 14 parks qualify, the result is **one exploratory external-dataset ecological analysis**, not E5 G4 calibration or an E4/eSDM predictive fit. Original E4/E5/E7/E7-C outcomes remain untouched. After a successful one-time opening, permanently pin the executable to its source SHA and preserve only aggregate outputs; no response-based categories, minimum camera threshold or panel-tuning.
