# NeoBat 35 source-disjoint botanical plants: joint original-raster input gate result

Date: 2026-11-19. Research-only, fixed before source reread:
`docs/replication/NEOBAT_35_SOURCE_DISJOINT_RASTER_JOINT_GATE_FROZEN_20261119.md`.

## Verified execution

- [Synthetic source/raster rules #44545069812](https://github.com/zuizui0223/esdm/actions/runs/44545069812) **PASS**.
- [Original source ZIP and joint 595-cell input audit #44545333829](https://github.com/zuizui0223/esdm/actions/runs/44545333829) **PASS**. Both original GBIF plant DOI ZIP and original WorldClim v2.1 BIO1/BIO12/elevation byte hashes and source-country precision cell counts reverified.
- Prior **three Colombia** *source-disjoint* model training counts for the exact fixed botanical sentinels replayed (35/565, 96/661, 62/650 after raster-validity screening); the separate old heldout AUCs were not refitted or used for selection in this source-only gate.
- Complete original 595 plant×country rows and 84 original bat×country folds preserved; raw GBIF rows, precise coordinates, cell IDs, dataset keys or raster values/pixels **not** written to GitHub. Full receipt `docs/replication/neobat/joint35_source_raster_trainability.json`, compact `docs/replication/neobat/joint35_source_raster_trainability_compact.json`.

## New strict joint prefit result (no ecological SDM)

| Source/raster training qualification | Verified quantity |
|---|---:|
| Frozen source-disjoint plant universe | **35** original author-candidate plants |
| Original withheld countries | **17** |
| Original plant×country trainability denominator | **595** |
| Trainable jointly after source embargo + BIO1/BIO12/ELEV nodata | **592 / 595** |
| Countries retaining all fixed 35 plant-model training inputs | **14 / 17** |
| Original 84 bat source + author fruit-link/N1 + background candidates BEFORE joint raster | **63 / 84** |
| Bat×country folds whose country additionally supports the complete 35-plant input under this joint test | **36 / 84** |
| Bat species in joint input candidate set | **11** |
| Countries in joint input candidate set | **10** |

The exactly three source+raster plant training stops at **20 focal observed source cells** threshold:

- Colombia (CO): *Cecropia sciadophylla* **19** strict post-source/raster training focal cells (103 background).
- Ecuador (EC): *Clarisia biflora* **19** focal cells (824 background).
- Mexico (MX): *Carica papaya* **17** focal cells (267 background), raw before rasters 18.
  
These are observed source-record cells, not verified botanical absences. Because the model specification requires **the same complete fixed 35-plant universe in every fold**, CO/EC/MX are **not** eligible for a full35 source-disjoint and raster-valid M1/M3 predictor matrix; this removes 12/4/11 respectively from the preceding 63 original bat folds. The 36 remaining candidate bat folds are located in BZ2, CR9, GT3, HN4, PA5, SV2, BR3, GF3, NI2, PE3. All 84 original bat folds continue to appear in the output.

## Meaning and next actual ecological gate

This establishes a reproducible, DOI-origin **input feasibility boundary**, not 35 fitted ecological plant suitability maps, biomass or fruiting abundance, or actual bat resource-dependent 3D habitat use. The WorldClim period 1970–2000 is not contemporary plant or fruit supply, and the botanical target background is still defined from GBIF source records. Even distinct original dataset IDs need not be independent observers or sampling designs. **M1/M3/N1 ecological heldout AUCs remain unestimated.**

Do not retrospectively delete three plants to recover Colombia, Ecuador or Mexico and claim a primary 35-plant test. Any smaller fixed species universe would be a separately labeled **exploratory design** requiring a new reference, effort, source and null audit, never a reinterpretation of the earlier 255-plant v1 contract.

A meaningful further biological experiment requires measured or independently calibrated botanical observation/availability (preferably fruiting abundance or vegetation/forest), source-audited bat pseudo-backgrounds and geographically independent validation, plus cross-fitted actual continuous plant predictor maps for the **36 input candidate** folds. Nothing in this source-only analysis establishes positive or negative ecological M3 superiority. Original main and unrelated frozen models remain unchanged.
