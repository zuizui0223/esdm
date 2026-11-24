# NeoBat resource-linked SDM — evidence and decision ledger (2026-11-19)

> **最新の現在地 (2026-11-19):** 下記の第1〜4節は記録時点の歴史的スナップショットです。初期の WorldClim STOP は原本SHAの誤転記と保存経路の不整合として解決済みです。現在の出典独立性・ラスタ・植物予測・bat shadow検定の判定は末尾 **第5節** を優先してください。**元の生態学的M3–M1/N1は依然として未推定**です。

**Current status:** DOI-backed source acquisition + original ZIP verification + complete raw-source quality screening are **complete**. Full-DOI country resource-input qualification is complete: 84/754 strict bat×country pairs (16 bats with at least 2 countries), with an independently required 20 outcountry recorded cells per linked plant. **No M1-vs-M3 ecological effect has been fitted or claimed.**

**Repository:** `zuizui0223/esdm`, research branch `design/neobat-trophic-sdm-phase1-20261119`, draft PR #244. **main remains unmodified.**

## 1. Completed evidence, strictly separated

| Gate | Empirically verified outcome | Receipt |
|---|---|---|
| NeoBat original study source | 2,571 total bat–plant interactions = 1,931 fruit + 640 nectar; 26 primary frugivorous bats; 709 distinct bat × fruit-plant links (of these 691 have GBIF strictly matched partner names) | `neobat/source_preflight.json`; `NEOBAT_LINK_INDEPENDENCE_AUDIT_20261119.md` |
| GBIF names, count-only preflight | 26 bat concepts, one independently verified Carollia spelling alias; 255 of 261 named fruit plants strictly matched, 6 unresolved | `neobat/gbif_search_preflight.json`; `neobat/plant_search_preflight.json` |
| NeoBat source-only country link recurrence | 6/12 observed-study countries qualify; 338 heldout documented fruit edges; observed recurrence 46.94% vs degree-preserving null 40.55% (+6.39 percentage points; Monte Carlo p=0.001). A separate source-run code implementation reproduced eight numerics. **Exploratory within one source universe** | `neobat/crosscountry_reproduction_result.json` and `neobat/crosscountry_reproduction_verdict.json` |
| Exploratory indexed-coordinate page sample | 14 fixed taxa, 55/55 country pages; ≥5 recorded 25-km cells in 4 countries for 4/4 bats and 7/10 plants. It is a **first-page lower bound**, not random sampling nor an independent external test | `neobat/spatial_country_lb.json` |
| Sample-limited resource input check | 9/16 bat-country combinations have ≥3 locally recorded candidate plants whose links can be obtained from ≥2 outcountry NeoBat source references. **Same country ≠ same cell** | `neobat/country_resource_gate.json` |
| Authenticated GBIF download for 26 bats | **SUCCEEDED**; 85,912 records; 529 source datasets; key `0001156-261118162104854`; DOI **10.15468/dl.nxu727** | `neobat/gbif_download_submission.json`; `neobat/gbif_download_doi_poll.json` |
| Authenticated GBIF download for 255 plants | **SUCCEEDED**; 367,988 records; 1,202 source datasets; key `0001157-261118162104854`; DOI **10.15468/dl.xwc5zf** | same receipts |
| Original GBIF ZIP verification | Both archives re-downloaded from GBIF and checked against exact original ZIP SHA-256, file type/50 TSV header fields. Bat SHA `fc94ff92a127ec22655733a0b0cdaf12b5b24794fcc0129532e8a1e49fe856f0`; plant SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b` | `neobat/gbif_archive_header_preflight.json` |
| Original complete-record GBIF source QC | **85,912 bats + 367,988 plants rows parsed.** All satisfy basic country/year/coordinate index/source screening in the original frozen query. **Known ≤12.5km reported uncertainty**: 18,351 bats (21.4%) and 89,718 plants (24.4%). **Uncertainty missing:** 67,121 bats (78.1%) and 275,378 plants (74.8%). Source records occur in 26/26 bat taxa, 251/255 plant taxa | `neobat/gbif_full_source_qc.json`; small `neobat/gbif_full_source_qc_summary.json` |
| Conservative geographic data quantity | ≥2 countries with ≥5 precision-restricted heldout cells and ≥20 precision-restricted outside-country cells: **19/26 bats** and **116/255 plants**. This is data *quantity*, not source independence, model performance or ecology | `neobat/gbif_full_source_qc_summary.json` |

**Corrections to earlier messages:** The former `AUTH_CONFIG_INCOMPLETE` status was superseded by an executed `AUTH_ENV_PRESENT_NOT_VERIFIED` receipt with no missing field names. The first attempted GBIF submit marker was a pre-job YAML parsing failure (0 jobs, 0 submitted requests); a distinct corrected marker successfully submitted exactly two requests, which both finished and now have DOIs. Do not repeat the authenticated GBIF POST. The timed-out all-page GBIF SEARCH pilot was superseded by the bounded sample and full DOI download.

## 2. In progress / not established

- Full-DOI precision-conditioned *resource link source-input* availability: script and deterministic tests in `scripts/neobat_full_doi_resource_country_gate.py`; result `neobat/gbif_precision_resource_country_gate.json` must be inspected before stating any qualified bat-country count. This is a **discovery source support gate** and not an SDM.
- No evidence so far of **M3 resource-link SDM outperforming M1 generic plant availability** in heldout country/region presence ranking. Not fitted.
- No independently verified plant abundance, fruiting time, true feeding behavior, within-cell bat–plant encounters, absolute occupancy, causal resource choice, or 3D niche mechanism.
- Raw GBIF geographic snapshots and bounded first pages were inspected for feasibility; they **must not** be misrepresented as truly unopened validation data.
- `batter` tracking taxa do not directly match the 26 primary NeoBat fruit guild cohort; `Phyllostomus hastatus` is an omnivore-specific **secondary** bridge only.

## 3. Next formal model gate

1. Integrate pinned CHELSA/WorldClim temperature & precipitation, independently sourced forest and terrain rasters, and survey effort/target-group background, all at a common 25-km EPSG:6933 grid. Keep raw parent files out of GitHub; retain immutable manifests/hashes.
2. Fit **plant relative suitability** for the 255 strict-match species (or report source/precision eligibility stops) with the same country withheld from **plant training**, not just bat training. Absent plant records are **not** verified plant absences.
3. From training-only NeoBat literature, construct `B(x)` (generic plant suitability) and `R_s(x)` (observed source-linked partner suitability). Reference/source publications touching the test country must be excluded from the link weights.
4. With spatially blocked and source-audited bat presence and target-group background, compare **M0 abiotic**, **M1 + generic plant**, **M3 + actual partner weights**, and **N1 degree-preserving rewired partner weights**. Same training labels, control effort, regularization, and heldout geography for every comparison. Store species/region effects and region-cluster uncertainty. The claim ceiling is *predictive incremental link information*, not causality.
5. Distinguish discovery/exploratory holdouts made from this now-open dataset from **genuinely independent external confirmation**. No model choice may be revised using a sealed validation response.

**Publication/promotional gate:** A positive result from the NeoBat source-network recurrence and data QC is not a positive 2D trophic SDM result. Do not merge this as one or upgrade an existing `batter`, `sdmr` or `esdm` confirmation claim.

## 4. Latest input qualification & model-source firewall (2026-11-19)

The DOI-backed **complete 26 bats × 29 countries = 754** source-input
matrix was executed successfully. With all records including missing
coordinate-uncertainty, 162 potential input pairs remain. With reported
coordinate uncertainty ≤12.5 km, at least 5 recorded bat cells inside
the candidate country and 20 outside, **and the same 5-inside / 20-outside
criterion for each source-linked fruit plant**, plus ≥3 distinct partner
plants and ≥2 training NeoBat source references, **84 pairs remain**.
Sixteen bat species have at least two such countries.

The earlier source-only program with no *plant outcountry 20-cell* gate
had 86 strict pairs and 18 bat species with two or more; two additional
pairs are no longer admissible: *Artibeus obscurus* × Brazil and
*Vampyressa thyone* × Costa Rica. This is a **prespecified input
feasibility refinement, not an outcome-based choice**.

- Full result: `docs/replication/neobat/doi_country_resource_input.json`.
- Small status: `docs/replication/neobat/doi_country_resource_compact.json`.
- Frozen all-species decision roster:
  `docs/replication/neobat/NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json`.
- Original-study embargo:
  `docs/replication/neobat/NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json`
  (all 200 NeoBat sites, 169 reference codes; 29 GBIF countries plus
  explicit US source). **M3 and N1 now require this exact source-sites
  reference embargo, even for publications absent from the fruit-only
  link table.**

A synthetic M0/M1/M3/N1 benchmark passed its software gate, but its
M3–M1 apparent gain did **not** exceed the degree-preserving N1 null;
that synthetic fixture is **not biological support**.

The climate raster source preflight remains blocked on frozen
WorldClim BIO12 member-byte SHA disagreement (the containing ZIP matches
its pinned SHA). Do not silently replace the expected raster digest or
start an ecological fit until source identity is diagnosed and the
abiotic/effort/reference predictors are fixed.

**Next main task:** qualify physical climate/forest/terrain raster
source identities, create leakage-free plant relative-suitability
predictions using only outcountry training presences, and then execute
the exactly frozen M0/M1/M3/N1 model on the discovery source. An
independent new period/source is still required for a confirmatory claim.

## 5. Latest source transport, source-disjoint plant qualification, and shadow contrasts (2026-11-19)

**All statements below are empirically recorded and remain separate from the original v1 ecological effect.**

| Stage | Fixed denominator and result | Claim ceiling / evidence |
|---|---|---|
| DOI-record source QC | 85,912 bat + 367,988 plant original GBIF rows; 84/754 strict initial species×country input candidates | `doi_country_resource_compact.json`, original DOIs; no true absences |
| Source-only 25km documented plant co-records | 82/84 of original bat×country folds have >=1 documented partner plant in same 25km recorded cell | `same_cell_source_support.json`; co-observation is **not feeding** |
| Original 106-plant exploratory v2 | 83/84 published partner citation and focal-N1 structural inputs; 79/84 when 26-bat target-group background is also required | `v2_106plant_reference_input_gate.json`, `bat_targetgroup_background_gate.json`; no SDM effect |
| Original 106 source/raster practical training | 15/17 countries fit all 106 after original WorldClim nodata; 51/84 source/raster/bat candidate fold intersections | `full106_raster_trainability_gate.json`; prefit quantity only |
| Original 106×17 botanical **GBIF source-rank** transfer | 647/1,802 plant×country heldout scores; extra abiotic AUC beyond local other-botanical-record intensity **+0.02539 country-equal**; record-intensity covariate strongly predictive | `plant_106x17_source_effort_transfer_compact.json`; **not real fruit abundance** |
| **Whole-GBIF datasetKey embargo** | Removing **every dataset touching withheld country** from all outcountry botanical training reduces 1,802 trainable pairs to **1,233**, and 677 source-test-eligible to **497**; only **35/106 plants** remain trainable across *all* original 17 countries | `plant_106x17_global_source_embargo_compact.json`, [PR #260](https://github.com/zuizui0223/esdm/pull/260); dataset ID disjointness is not independent field effort |
| Same heldout CO **three botanical source-disjoint model refits** | Combined reported-source rank AUC, old→source-disjoint (same CO test rows): *Cecropia obtusifolia* 0.7318→0.7420, *Ficus insipida* 0.7667→0.7727, *Piper aduncum* 0.8393→0.7729 | `CO_three_plant_disjoint_source_AUC.json`, [PR #263](https://github.com/zuizui0223/esdm/pull/263); post-hoc observational robustness, not actual availability |
| Fixed source35 frugivory input | Of all original **84**, **66** retain >=3 published partners / >=2 independent outcountry author references and focal-N1 2-edge swapping; **63** also have bat target-background data, across 14 bat species / 13 countries | `source35_bat_literature_N1_input_gate.json`, [PR #264](https://github.com/zuizui0223/esdm/pull/264) |
| **Source35 + original climate raster nodata jointly applied** | **592/595** fixed plant×country training sets have >=20 valid focal and target-background source cells; 14/17 countries retain all 35; strict intersection with original 84 bat folds leaves **36/84 across 11 bat species / 10 countries** | `joint35_source_raster_trainability_compact.json`, [PR #268](https://github.com/zuizui0223/esdm/pull/268); **not yet 35 fitted ecological plant SDMs** |
| Separate, weaker **S0/S1/S3/SN1 climate-only shadow** | 49/51 available 106-plant bat source-rank fits; mean S3−S1 **−0.00569 AUC**, mean S3−rewired SN1 **−0.00800 AUC**. El Salvador exclusion post-hoc yields S3−S1 mean −0.00061 across 47. | `shadow_climate_only_51fold.json`, [PR #266](https://github.com/zuizui0223/esdm/pull/266). **No overall source-linked identity advantage** in this *shadow* source-recording proxy; not the v1 ecological M3 or direct mechanism test |

### Corrections and nonpromotable claims

1. **Superseded early climate stop:** corrected original WorldClim BIO1/BIO12 and independently SHA-checked elevation geoheaders are verified in `abiotic_terrain_forest_source_preflight.json`; the earlier failed Actions conclusion arose from an incorrect corrected-vs-original receipt path even though original raster verification succeeded. ESA WorldCover **one-tile only** accessibility verified; 17-country forest fractions not derived. The 1970–2000 climate baseline is not contemporaneous fruiting.
2. The observed **+0.0254** botanical source-rank abiotic increment does **not** demonstrate independent species occurrence or fruit abundance. The full-source datasetKey-embargo audit reduces previously assumed plant training coverage substantially, and source-key disjointness alone does not guarantee different institutions, observers, events or effort.
3. The 106-plant **shadow S3** result does not support a consistent partner-identity benefit, but it is not a true absence of ecological fruit-resource dependence either. It lacks independent plant abundance, measured sampling effort and complete forest, and shares previously opened GBIF source structure with the earlier botanical analyses. Do **not** promote its nominal individual-fold SN1 tests as discoveries or retune same records to chase positive shadow results.
4. **Original ecological primary** M3−M1 and M3−N1 bat heldout performance remain `null / NOT ESTIMATED`; no actual complete, independent 255-plant resource-suitability models, measured feeding events or direct 3D resource mechanism are available. Parent PR #244 remains draft; **main is unchanged**.

### Next primary action (one goal)

Construct externally sourced or separately calibrated **botanical availability / survey-detection** and vegetation/forest predictors, then generate one consistent source-blocked **35-plant** cross-fitted 25km raster score set for the **36 original prefit source+climate eligible bat×country folds**, with the 84 original denominator and explicit failures preserved. Compare M1/M3/N1 only on identical training/test bat source rows and plant score rasters, with source provenance/folds frozen. At this stage even such a fit would be an **exploratory observational test**, not independent proof of food availability or causal interaction. For a confirmatory universal claim a genuinely independent botanical and bat observation source/period is necessary.

