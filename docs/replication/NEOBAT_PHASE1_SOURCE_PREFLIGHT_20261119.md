# NeoBat phase-1 source preflight receipt — 2026-11-19

**Stage:** inspected interaction-predictor source; **bat/plant GBIF response and prediction data not downloaded**, no biological effect or predictive performance measured.

## 1. Source identity and access

Paper: Florez-Montero et al. 2022, Ecology 103:e3640, DOI `10.1002/ecy.3640` (publisher Supplement and Zenodo `10.5281/zenodo.4894176`). The 2026-11-19 automated attempt to access publisher ZIP via web returned HTTP 403 and Zenodo record was not retrievable via that route.

The **authors' original GitHub supplement** is publicly accessible at `https://github.com/gflorezm/NeoBat_Interactions`. The Global Biotic Interactions mirrored version is `https://github.com/globalbioticinteractions/NeoBat_Interactions`. GitHub content **blob SHA matches byte-identically in both repositories** for all three published data tables:

| File (under Data/) | Git blob SHA | Header dimensions | CSV data rows |
|---|---|---:|---:|
| `NeoBat_Interactions_Records.csv` | `71f179a152a262d7a98d7bb4e633cf136bc39f98` | 15 | 2,571 |
| `NeoBat_Interactions_Sites.csv` | `f9672a8b5542b8f4ecd3434ca798756f865df541` | 26 | 200 |
| `NeoBat_Interactions_References.csv` | `9061aa7a2b2f44a1aa23273a87cba6183af823b1` | 4 | 169 |

No claim of bitwise identity with the inaccessible Wiley ZIP / Zenodo archive. Source-level attribution and version pinning can use the publicly readable **authors' repository**, not third-party GloBI taxonomic augmentation.

## 2. Actual interaction rows

- Original records: **2,571 TOTAL** = **1,931 Frugivory** + **640 Nectarivory**. The article's abstract can be misread as 2,571 fruit records; this receipt resolves that ambiguity from the source CSV.
- Frugivory: 74 raw `CurrentBatSpecies` strings; 383 raw `CurrentPlantSpecies` strings; 110 unique `SiteCode` and 104 unique `RefCode`. Source site and reference joins have **0 missing keys**.
- Strict preliminary binomial-looking filter (two tokens, each matching `[A-Z][a-zA-Z-]+` + `[a-z-]+`, exclude obvious `sp`, `indet`, `cf`, `aff`, `unidentified`): **1,327 fruit rows**, 59 bat strings, 283 plant strings. This is **not an accepted-taxon checklist**; spellings and synonyms still need independent taxonomic validation.
- Frugivory source sites span **14 country labels**. Among 110 fruit sites, 72 have `Precision=Precise`; 38 have `Precision=Not precise`. All 110 have nonempty numeric coordinate fields, but a numeric coordinate is not proof of fine spatial accuracy. **71/110** fruit sites have `SamplingEffort` missing or `NA`; exclude use of interaction `Weight` as absolute food-use abundance.
- Among all 200 sites: 123 `Precise`, 77 `Not precise`; 149 have missing `SamplingEffort`. `YearStart` and `YearEnd` are both four-digit for 185/200 sites; observed site start years range 1960–2006. Source literature cited in the paper spans 1957–2007.
- Overall raw `Weight` is NA in 1,426/2,571 records; otherwise heterogeneous values. Primary analysis uses **binary observed link**.

## 3. Candidate bat taxa (network-only, before GBIF eligibility)

Source-only filter: species-level-looking bat and plant names, >=3 distinct fruit partner strings, >=2 independent `RefCode`, >=2 distinct countries with source sites. **31 candidate bats** meet the broad *fruit-use* conditions, but **26 candidates** meet the same network criteria **and** have all included records classified as `TrophicGuild=Frugivore` in this CSV. The 26 are the phase-1 primary-frugivore candidate roster; the other 5 remain sensitivity-only fruit consumers. No bat occurrence or accepted-name cross-check was performed.

| Candidate | Fruit rows | Distinct linked plant strings | Independent references | Countries | Precise source sites |
|---|---:|---:|---:|---:|---:|
| *Carollia perspicillata* | 239 | 125 | 43 | 10 | 26 |
| *Artibeus lituratus* | 184 | 99 | 33 | 8 | 22 |
| *Artibeus jamaicensis* | 125 | 60 | 28 | 5 | 17 |
| *Sturnira lilium* | 47 | 37 | 14 | 2 | 13 |
| *Artibeus planirostris* | 76 | 61 | 13 | 5 | 6 |
| *Carollia brevicauda* | 32 | 28 | 9 | 5 | 5 |

This is **not a ranked post-hoc species selection**: all candidate taxa satisfying predeclared response and taxonomic gates will enter, with equal species weight at analysis.

## 4. Column-level join contract

- **Records**: `IDCode, SiteCode, RefCode, CurrentBatSpecies, CurrentPlantSpecies, Interaction, TrophicGuild, Weight`; other attributes are available.
- **Sites**: `SiteCode, RefCode, Country, Latitude, Longitude, Precision, YearStart, YearEnd, SamplingEffort, SamplingMethod, Ecoregion`; plus study and environmental metadata.
- **References**: `RefCode, Author, Year, Reference`.

Link `Records.SiteCode -> Sites.SiteCode`; `Records.RefCode -> References.RefCode`; also verify `Records.RefCode` agrees with the joined site `RefCode` rather than assuming it. **Checked: 0 conflicting source RefCode joins among 1,931 fruit rows**. Do not convert `Precision=Not precise` into a 25-km resolved point without uncertainty checks. Treat study/station/reference as correlated observational units.

## 5. Current terminal stage

**Source/interaction-schema preflight: PASS for repository availability and essential joins.**  
**Independent bat/plant occurrence + environmental raster preflight: NOT RUN.**  
**Eligible spatial folds and independent GBIF DOI receipts: NOT RUN.**  
**Models M0/M1/M2/M3/N1/N2: NOT FIT.**  
**Predictive ecological support: NOT EVALUATED.**

Next executable gate: DOI-bearing bat and plant GBIF downloads with pinned snapshots, independent footprint and accepted-name crosswalk, coordinate quality and region/fold denominator *before* inspecting held-out performance. No promotion of esdm E4/E5 claims.

## 6. Reproducible next gate (2026-11-19)

The work branch contains `scripts/neobat_gbif_metadata_preflight.py`, `tests/test_neobat_gbif_metadata_preflight.py` and `.github/workflows/neobat-readonly-preflight.yml`. The isolated workflow is configured to verify immutable author-source Git blob SHA, issue read-only GBIF species-name and occurrence **count/facet requests**, and save aggregate receipts under `docs/replication/neobat/` if network/Actions permissions permit. It must never be interpreted as a DOI-bearing occurrence download, 25-km spatial-cell denominator, or performance result. The existence of this workflow does **not** imply that it has run successfully.
