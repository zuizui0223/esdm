# S14: Is species-relative *recorded* diel ordering transferable among African protected-area camera networks?

**Design frozen before inspecting Safari 2024 expansion animal/timing outcomes (2026-11-11).** Separate observational cross-reserve study, not E4 model repair, not an E5 detection calibration and not a post hoc E7-C threshold relaxation.

## Ecological question

Earlier E7 revealed that **wet–dry *changes*** in a species pair's recorded night/midday odds were not reliably transferred between Serengeti collection seasons. Could a simpler underlying trait — the **baseline relative night/midday recording order of sympatric mammal species** — generalize across *different ecosystems*? The target is a **within-camera, across-reserve species-relative diel ranking**, not climate causality, competition, population abundance, or true passage time independent of camera detection.

## Untouched independent response and 14-project split

Source: [LILA BC Snapshot Safari 2024 Expansion](https://lila.science/datasets/snapshot-safari-2024-expansion/), published 2024, containing 4,029,374 image metadata records from 15 Snapshot Safari projects, 1,824 camera-location IDs and COCO Camera Traps species labels. Use metadata only, **not images**, and cite the LILA dataset/its CDLA permissive licence. Official public zipped metadata:

`https://storage.googleapis.com/public-datasets-lila/snapshot-safari-2024-expansion/snapshot_safari_2024_metadata.zip`

**Exclude "SER" (Snapshot Serengeti) completely**: it overlaps earlier E7's Serengeti biological source and must not be called independent confirmation. Fourteen other parks are fixed **before source opening**. Use park codes from camera filename prefix, with `project+location+sequence` identifying a sequence, not one image per frame.

- Discovery 7: `APN,CDB,ENO,KAR,KGA,KRU,LEC`
- Heldout validation 7: `MAD,MLP,MTZ,NIA,PLN,RUA,TSW`

These are different protected-area projects but geographically nonrandomized and protocol/ecosystem differences remain possible. APN/KRU belong to the same neighboring ecological complex and both are discovery. The heldout label is **different reserve networks**, not a novel year, biome-specific randomization, or sensor-independent detector calibration.

## Fixed animal treatment and date/clock bins

1. Use the COCO image ID → sequence ID, source `location`, recorded `datetime` and source filename. Deduplicate annotations to at most **one** (`project, location, seq_id, normalized_mammal_label`) record. The clock time is the **earliest valid image datetime within the sequence**. Do not count multiple burst images as independent animal visits.
2. Exclude nonmammal, people, vehicles, empty frames and domestic livestock via a **source-independent whitelist of wild African mammal category aliases fixed in code**. Species-sex aliases for lion are pooled to one category; ambiguous or unidentified labels are discarded and counted. Use local recorded clock hours without inventing an astronomical solar correction or UTC conversion.
3. Deep night = **21:00–03:59**; midday = **10:00–15:59**. Omit remaining clock times including uncertain dawn/dusk. These windows have different durations; within-camera species *ratio of night/midday odds* cancels a taxon-common period-effort term but does **not** identify species-specific detection differences.
4. **Discovery-only panel selection:** choose 12 eligible mammal labels ranked by the count of discovery parks with ≥5 physical cameras containing at least 8 eligible *full-day* distinct sequences for that taxon per camera (ties: number of such cameras, then original species-wide distinct sequences and lexicographic label). Do not use wet/dry outcomes, clock-time odds or validation records for selecting the taxa.
5. Evaluate all **66 unordered** pairs of those 12 discovery taxa, including every ineligible park/pair; no outcome-selected pair substitutions or new cutoffs.

## Fixed project-level estimand and generalization

For each fixed pair of taxa (i,j), at a physical camera **within one park**, require at least **8 unique sequence events within the selected deep-night + midday windows for each taxon**. Estimate the within-camera log contrast as

`c_ij,s=log[(n_i+0.5)/(d_i+0.5)]-log[(n_j+0.5)/(d_j+0.5)]`.

**The +0.5 Jeffreys continuity choice is predeclared for this *new* baseline-diel study**, permitting strongly diurnal/nocturnal species to contribute without treating an observed zero as a non-operating detector. It does NOT modify E7-C's frozen, stricter no-pseudocount seasonal endpoint. Reference exposure in each daypart was not independently verified; this is explicitly a recorded-sequence descriptor. Pair-level within-camera comparisons have the same nominal detector and sampling context.

For each project, take the **equal-camera median** of its camera-level contrasts, provided ≥5 informative distinct physical camera locations; otherwise the project/pair is `NOT_ESTIMABLE` and is retained in output. No image/event-level p-values and no reweighting to maximize apparent generality.

For each pair, calculate a **discovery 7-park median** of project effects if ≥3 discovery parks are estimable, and a **validation 7-park median** if ≥3 validation parks are estimable, then report:
- Number of pairs estimable in discovery, validation, both;
- Number with same directional sign across discovery and validation, and number with both *leave-one-park-out* medians remaining on the same nonzero side of zero, only if ≥4 estimable projects in each split;
- Predictive skill of unchanged discovery project-median contrasts on those fixed common eligible validation pair effects, against the zero-relative-contrast baseline, **descriptive only**;
- The entire 66-pair matrix with each project support, recorded effect and refusal reason; exclude all raw image, sequence and camera identifiers from published artifacts.

The natural baseline could already have species-specific rankings (large carnivores versus ungulates). A repeatable clock-time rank across reserves would be ecologically suggestive *only as an observation-level trait* until sensor-position and detector comparisons are calibrated. A failure to transfer may reflect context, unmatched species communities, season, detector settings or image selection rather than ecological plasticity.

## Fixed source/quality/firewall rules

- Before reading category/time labels: confirm exact source URL, downloadable archive format and SHA-256. The dataset has no preverified SHA here: **record the observed digest**, and require that same digest in any later claimed reproduction; do not fabricate one.
- Reject unknown project aliases and missing `location`/`seq_id`; exclude and audit annotations lacking image identity. If enough project/category support is missing, **stop and report unsupported**; no postresult change in park split, 12-taxon size, 8-event/5-camera/3-park thresholds, clock windows, or category mapping.
- A new explicitly titled one-time GitHub workflow may read the public metadata ZIP (no image content). Run synthetic tests first and publish only aggregate per-park and pair summaries with source hash, sample counts and exact terminal status. Prevent repeated wildlife opening on PR updates.
- The original E4 predictive activity failure, E5 G4 0/17 qualification, E7 23/46 seasonal-effect direction concordance, and E7-C 1/66 vs 9/66 complete-cell support are all **frozen and untouched**. No new model generation, no causal biotic interaction claim, and no inference from a recorded zero to an individual animal's absence.

### Primary success criterion

**What is being tested:** Whether a discovery-defined *observational species-relative night/midday order* is directionally reproducible at wholly different protected-area camera networks for at least three observed parks per partition. If no pair qualifies in both, record the **insufficient cross-project species overlap** rather than changing design. Do not call a high within-dataset agreement an independent detection-calibrated ecological law.
