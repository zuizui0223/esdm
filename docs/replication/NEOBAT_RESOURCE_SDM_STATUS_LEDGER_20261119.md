# NeoBat resource-linked SDM — evidence and decision ledger (2026-11-19)

**Current status:** DOI-backed source acquisition + original ZIP verification + complete raw-source quality screening are **complete**. Full-DOI precision-conditioned bat × country fruit-link qualification is in progress. **No M1-vs-M3 ecological effect has been fitted or claimed.**

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
