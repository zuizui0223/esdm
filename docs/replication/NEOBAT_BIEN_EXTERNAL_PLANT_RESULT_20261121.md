# NeoBat: actual BIEN CR/PA external plant diagnostic

Date: 2026-11-21 (Asia/Tokyo). The actual run completed at 23:42 JST.

## Result and its practical meaning

The frozen climate-only plant component was replayed for **all 106 plants in
both countries (212 fits)** and scored against complete native-only BIEN plot
tables. The primary comparison has only **two sampled 25 km cells in CR and
three in PA**. Its **six CR and four PA estimable taxon-frame comparisons each
contain one focal-positive cell and one background cell**. These are extremely
sparse geographic contrasts, even though the underlying tables contain 30,339
plant-record rows.

All returned records have missing coordinate-uncertainty values. The
predeclared known-precision sensitivity therefore contains **zero eligible
records and no AUCs**. This is missing information; it does not mean the
coordinates are inaccurate or that the model has zero predictive performance.

The computation is complete, but these results do not establish reliable
external predictive accuracy. The observed rankings are exploratory; original
source independence also remains unresolved. This result does not estimate
ecological M3, bat-model improvement, occupancy, fruit yield, or absence.

## 1. Conditions fixed before scores

The [comparison specification](NEOBAT_BIEN_EXTERNAL_PLANT_DIAGNOSTIC_FROZEN_20261121.md)
was committed at
[`32aa43987b5ac4e2ce4c279504ddcc9732bd0b0c`](https://github.com/zuizui0223/esdm/commit/32aa43987b5ac4e2ce4c279504ddcc9732bd0b0c)
before any BIEN predictions. No taxa, countries, thresholds, frames or date
modes were changed after seeing the results.

The adapter reuses the original country-excluded training selection and
climate-only plant model from `d65817fcb3c39060ed544261c291d76a198299c6`. It
verifies the original plant ZIP, raster hashes, all 212 positive/background
training counts, and actual training-cell membership. All models are fitted
before external cells are predicted. This is a fixed-specification replay;
historical fitted weights were not available as serialized artifacts.

The complete native-only country tables supply the sampling background,
including plots without any focal-taxon match. Comparisons preserve source,
method, area and inclusion-metadata frames. Known focal-positive cells anywhere
in the country are removed from that taxon's background across frames and date
modes. The exact original training-cell union is also removed from evaluation.
Repeated stems, plots and visits in a cell do not increase cell weights.

The run found **zero training-overlap exclusions and zero raster-invalid
exclusions** among candidate taxon-frame comparisons. Invalid geographic
coordinates are handled earlier and are reported separately below. These
zero-overlap counts do not prove that the original field data sources differ.

## 2. Actual acquired data and effective geographic support

Data: BIEN R package **1.2.8**, database **4.2.8**, database release date
**2023-06-27**. The prior receipt's numeric value `19535` represents this R Date;
it is not a database build identifier. Actual acquisition counts reproduce the
earlier CR/PA counts exactly.

| Returned or derived quantity | CR | PA |
| --- | ---: | ---: |
| Full country plant-record rows | 21,949 | 8,390 |
| Focal matched record rows | 557 | 974 |
| Focal taxa with any exact-name match / 106 | 17 | 22 |
| Full-table hierarchical plot labels | 42 | 36 |
| Returned method/area/source frames | 4 | 6 |
| Records with invalid or missing geographic coordinates | 623 | 298 |
| Records with unknown observation year | 6,432 | 309 |
| Records with observation year before 2000 | 0 | 3,322 |
| Records with unknown coordinate uncertainty | 21,949 | 8,390 |

Plot labels and record rows are not independent geographic samples. All ten
returned frames have at least one populated method field; this does not
certify equal survey effort or complete detectability. CR has one frame for
each of its four sources. PA includes Gentry, TEAM and four CTFS area frames
(0.16, 0.32, 1.0 and 5.96 ha).

| Predeclared mode | CR eligible records | CR sampled cells | CR estimable taxa | PA eligible records | PA sampled cells | PA estimable taxa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2000–2025 primary; unknown precision disclosed | 14,973 | 2 | 6 | 4,613 | 3 | 4 |
| 2000–2025; known uncertainty <=12,500 m | 0 | 0 | 0 | 0 | 0 | 0 |
| Historical/undated descriptive; year <=2025 or unknown | 21,326 | 6 | 14 | 8,092 | 6 | 14 |

Eligible records and sampled cells in this table are the full mode-specific
sampling frame before taxon-specific exclusions. Estimable taxa require an
actual retained positive/background contrast within at least one frame.

### All 212 results remain in every mode

| Mode and country | Estimable | Matched but no eligible positive cell | Positive support but no within-frame contrast | Never matched: unknown |
| --- | ---: | ---: | ---: | ---: |
| Primary CR | 6 | 10 | 1 | 89 |
| Primary PA | 4 | 10 | 8 | 84 |
| Known-precision CR | 0 | 17 | 0 | 89 |
| Known-precision PA | 0 | 22 | 0 | 84 |
| Historical/undated CR | 14 | 0 | 3 | 89 |
| Historical/undated PA | 14 | 0 | 8 | 84 |

Each country row sums to 106. Unknown and non-estimable results retain null
metrics; they are not converted into ecological absences or zero AUCs.

## 3. Primary rankings: every estimable comparison

All primary estimable comparisons come from TEAM: Volcán Barva in CR and
Barro Colorado Nature Monument–Soberania National Park in PA. Every row below
uses **one positive cell and one background cell within its own source frame**.

| Country | Focal taxon | Positive cells | Background cells | AUC |
| --- | --- | ---: | ---: | ---: |
| CR | Calophyllum brasiliense | 1 | 1 | 1.0 |
| CR | Cecropia insignis | 1 | 1 | 1.0 |
| CR | Cecropia obtusifolia | 1 | 1 | 1.0 |
| CR | Clarisia biflora | 1 | 1 | 1.0 |
| CR | Socratea exorrhiza | 1 | 1 | 1.0 |
| CR | Turpinia occidentalis | 1 | 1 | 1.0 |
| PA | Anacardium excelsum | 1 | 1 | 1.0 |
| PA | Cecropia obtusifolia | 1 | 1 | 0.0 |
| PA | Ficus obtusifolia | 1 | 1 | 0.0 |
| PA | Poulsenia armata | 1 | 1 | 0.0 |

With one pair, AUC records only the direction of that pair's ordering (or 0.5
for a tie). An AUC of 1.0 here does not establish stable accuracy. An AUC of
0.0 records a reversed ranking for this comparison; it does not imply absence
or zero suitability. The taxa share a very small geographic frame, so these
rows are not ten independent geographic replications. No pooled overall AUC,
confidence interval, significance test or superiority threshold is reported.

The historical/undated mode has **25 estimable taxon-frame contrasts in CR and
18 in PA**, covering 14 taxa per country. These retain only six sampled cells
per country, with one or two positive cells and one to three background cells
per estimable contrast. Its full per-frame AUCs and separate descriptive frame
means are in the result JSON. This broader date mode does not replace the
primary result or resolve unknown coordinate precision.

## 4. Direct datasource bibliography lookup completed

The successful query retrieved the six source rows and their three direct
proximate providers using an explicit public-field allowlist. No contact
values were queried. The source/proximate relationships are now directly
observed in the database:

| Specific BIEN dataset ID | Dataset | Direct proximate provider ID/name | Specific citation | Specific DOI | Specific source URL |
| --- | --- | --- | --- | --- | --- |
| 18 | Volcán Barva | 392 / TEAM | Missing | Missing | Missing |
| 27 | Brad Boyle Forest Transects | 391 / SALVIAS | Missing | Missing | Missing |
| 37 | La Selva Secondary Forest Plots | 391 / SALVIAS | Missing | Missing | Missing |
| 40 | Gentry Transect Dataset | 391 / SALVIAS | Missing | Missing | MOBOT Gentry website |
| 59 | CTFS Panama Plots | 395 / CTFS | Missing | Missing | Missing |
| 66 | Barro Colorado Nature Monument–Soberania National Park | 392 / TEAM | Missing | Missing | Missing |

The proximate-provider rows contain the general SALVIAS (Enquist and Boyle,
2012), TEAM (Fegraus, 2012), and CTFS–ForestGEO (Anderson-Teixeira et al., 2015)
network citations and websites. We acknowledge these providers and the named
underlying datasets. Their supplied citations and `acknowledge` access
conditions are preserved in the acquisition receipt.

The returned bibliography supplies no direct GBIF datasetKey or DOI crosswalk
for the six specific datasets. The earlier source-registry lookup is therefore
no longer blocked by connectivity; its actual metadata is insufficient to
prove observation-level independence. No direct source-equivalence or source-
disjointness conclusion is added to the
[original GBIF lineage assessment](NEOBAT_BIEN_CR_PA_SOURCE_LINEAGE_20261121.md).

## 5. Evidence, reproducibility and verification

- [Untouched acquisition receipt](neobat/bien_external_acquisition_receipt_20261121.json).
- [Untouched diagnostic result, all 212 entries per mode](neobat/bien_external_plant_diagnostic_20261121.json).
- Successful [run 44915110088](https://github.com/zuizui0223/esdm/actions/runs/44915110088),
  job `136878947633`, executed commit
  `51a5d9cdd23730b5d19f7f69615c0a1efed99ea0`.
- Artifact `14711665750`, containing exactly the two JSON files above.

| Evidence | SHA-256 |
| --- | --- |
| Frozen comparison specification | `bdbf943b87b23bc8868d0fc45d8e0bf1e2ea2bfaba0e906c7492902e8858eb77` |
| Artifact ZIP | `04e8aa982e57df579a29f8651f9557682b32f04bdebb277bc360551e9a754226` |
| Original acquisition JSON | `1a1635c23f3100d9794a55eb3f56bf96b5f5285cfffe5e97db114acee9053863` |
| Original diagnostic JSON | `fa8342ab203152b8ec347653961612142b19a9e44ca20864904b540e7ed1f788` |

The run passed 17 focused Python tests and the R acquisition tests before
querying BIEN. Successful receipt statuses, all model training counts, all
result denominators, frame counts, exclusion counts, hashes, and public output
content were subsequently inspected. Numerical versions were numpy 2.2.6,
scikit-learn 1.7.2, rasterio 1.4.3 and pyproj 3.7.2, matching the original four
pins; SciPy 1.18.1 is also recorded. The preceding local adapter comparison
against the original helper under the same local runtime had zero prediction
difference; it was not a comparison against archived historical fitted weights.

The workflow uploads only the two named aggregate files and removes temporary
raw inputs. No raw coordinates, plot/cell identifiers, individual predictions
or fitted coefficients are published. The result and documentation commit does
not trigger another data acquisition or model fit.

The concrete remaining evidence gaps are geographically broader comparable
external observations, defensible coordinate-uncertainty information, and
observation/source identifiers connecting the original survey publications.
Increasing record counts within these same few cells cannot resolve the
geographic replication limitation.
