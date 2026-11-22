# NeoBat: BIEN external plant diagnostic across ten prelisted countries

Date: 2026-11-22 (Asia/Tokyo). The eight-country run completed at 10:51 JST.

## Result and its practical meaning

**The execution is complete for all ten prelisted countries: 848 newly
replayed plant fits and 212 reused CR/PA fits, with all 1,060 taxon-country
entries retained in every mode.** The [validated combined summary](neobat/bien_fixed10_summary_20261122.json)
accounts for 126,080 plant-record rows. Geographic coverage expands, but the
primary dated comparison remains small: **14 taxon-country entries produce
14 estimable taxon-frame contrasts, of which 11 contain just one positive
and one background cell**.

Brazil adds the four new primary contrasts, with eight sampled cells before
taxon-specific exclusions. The other seven new countries add no primary
AUCs. Ecuador, French Guiana and Nicaragua have no recorded observation
years. Guatemala, Honduras and El Salvador returned schema-valid empty
country tables. Their 318 taxon-country entries remain unknown in each mode;
these empty query results are not evidence that the plants are absent.

Peru illustrates why record counts and pooled country coverage cannot replace
within-frame comparisons. Its primary mode has 2,654 eligible records and two
sampled cells, but the cells belong to different frames. All 16 positive
taxon-frame rows, covering 15 taxa, have one positive and zero background
cells; no primary AUC is estimable. The historical/undated mode has broader
support: 34 sampled cells, 26 estimable taxa and 53 retained contrasts.

Across all ten countries, the historical/undated mode has **85 estimable
taxon-country entries and 133 contrasts**. It also contains a real
training-overlap exception in Peru:
**two positive and six background exclusion events**, summed over taxon-frame
comparisons. These exclusions are applied before AUC calculation and do not
mean eight distinct geographic cells. Details are reported below. Every
returned record has unknown coordinate uncertainty, so the
known-precision sensitivity has no eligible records or AUCs.

The broader historical support is useful descriptive evidence about relative
plant-climate rankings. It does not replace the primary date window or
establish reliable independent predictive accuracy. Source independence
remains unverified; ecological M3, bat improvement, occupancy and fruit
resources remain outside this diagnostic.

## 1. What was fixed, and what this extension evaluates

The [frozen extension](NEOBAT_BIEN_FIXED10_EXTERNAL_EXTENSION_FROZEN_20261122.md)
was committed at
[`32d949b8b63c2adfa4918fda22e842a05cd58e72`](https://github.com/zuizui0223/esdm/commit/32d949b8b63c2adfa4918fda22e842a05cd58e72)
before retrieving or scoring the eight additional country tables. Its scope
comes from the existing [106-plant, ten-country manifest](NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json):
**BR, CR, EC, GF, GT, HN, NI, PA, PE and SV**. Countries were not chosen using
their observed BIEN coverage or rankings.

The new execution covered **BR, EC, GF, GT, HN, NI, PE and SV**, with 106 fixed
country-excluded plant specifications per country. The previously opened
**CR and PA** results remain in their original receipt files and are reused.
The completed accounting is therefore **848 new fits plus 212 reused fits**, and
**1,060 taxon-country entries in each of three modes**. The extension was
specified after the CR/PA results were known; the ten-country panel is an
exploratory follow-up, not a new confirmatory test.

The adapter reuses the original helper functions and training-count receipts
at immutable design commit
[`d65817fcb3c39060ed544261c291d76a198299c6`](https://github.com/zuizui0223/esdm/commit/d65817fcb3c39060ed544261c291d76a198299c6).
This is a fixed-specification replay because the original fitted weights were
not archived. The component belongs to the 106-plant weak-shadow analysis. It
does not estimate ecological M3, a bat response, plant occupancy, fruit
production or the effect of plants on bat prediction.

The three predictors remain BIO1, BIO12 and elevation, sampled at the centers
of the original 25 km EPSG:6933 cells from WorldClim v2.1 10-arcminute rasters
(climate baseline 1970–2000). Each model uses the original training-only
`StandardScaler` and balanced logistic regression: `C=1`, `solver=lbfgs`,
`max_iter=400`, `random_state=20261119`. The original positive/background
training selection and its minimum of 20 rows in each class are unchanged.
That original fitting requirement is not an added minimum for external
comparisons.

Training excludes the held-out country's original observations and the
original cross-country cell embargo. The adapter checks the original
positive/background counts and exact fit-row cell membership for every
requested model. Each country's 106 fits finish before its BIEN cells are
predicted. No BIEN labels or outcomes enter fitting, and no bat outcome file
is opened.

## 2. Full-country acquisition and the unchanged comparison

Acquisition uses official
`BIEN_plot_country(all.metadata=TRUE, natives.only=TRUE, cultivated=FALSE)`.
The full returned country table supplies the sampling frame, including plant
records and plots without any focal-taxon match. Fixed-name matching uses the
same 106 names and existing whitespace normalization; there is no new
taxonomic reconciliation.

Comparisons remain within source/dataset, method, plot-area and taxonomic or
growth-form inclusion-metadata frames. Missing metadata remains explicit.
Matching metadata does not establish homogeneous effort, complete inventories
or equal detectability. Stems, plots and visits are collapsed to unique cells
for each taxon and frame. A cell with any known focal record in the country is
excluded from that taxon's background, including when that focal record belongs
to another frame or is ineligible under the current date mode. Each taxon's
exact original training-cell union is removed from both comparison classes.

AUC is the fraction of positive-versus-background score pairs ordered in the
expected direction within one frame, with ties contributing one half. A
contrast exists only when at least one retained cell occurs in each class.
There is no new minimum-plot or minimum-taxon filter. Background cells mean
that other plants were recorded there; they are not demonstrated absences of
the focal plant.

The original [comparison specification](NEOBAT_BIEN_EXTERNAL_PLANT_DIAGNOSTIC_FROZEN_20261121.md)
retains three separate modes:

| Mode | Observation year | Coordinate uncertainty |
| --- | --- | --- |
| Primary | Known year from 2000 through 2025 | Known values must be <=12,500 m; unknown values remain disclosed |
| Known-precision sensitivity | Known year from 2000 through 2025 | A known value <=12,500 m is required |
| Historical/undated descriptive | Year <=2025 or unknown | Known values must be <=12,500 m; unknown values remain disclosed |

Invalid geographic coordinates and invalid nonmissing precision values are
excluded under the same rules as before. Dates and precision are never inferred
from a source title, publication date or bibliography. The descriptive mode
does not replace the primary result when dated support is unavailable.

## 3. Country coverage and effective geographic support

The following coverage values are observed counts in the preserved receipts
and combined summary. CR and PA are reused from the prior run; the other
eight countries come from the new run. The full tables contain 126,080 record
rows, including 2,811 exact-name focal records across 100 taxon-country pairs.
They form 36 country-scoped metadata frames, of which 35 have method metadata
and one does not.

| Country | Evidence | Record rows | Matched taxa /106 | Frames | Unknown year | Invalid/missing coordinates |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| BR — Brazil | New | 55,715 | 7 | 4 | 887 | 5,319 |
| CR — Costa Rica | Prior | 21,949 | 17 | 4 | 6,432 | 623 |
| EC — Ecuador | New | 3,126 | 21 | 5 | 3,126 | 137 |
| GF — French Guiana | New | 105 | 1 | 1 | 105 | 8 |
| GT — Guatemala | New | 0 | 0 | 0 | 0 | 0 |
| HN — Honduras | New | 0 | 0 | 0 | 0 | 0 |
| NI — Nicaragua | New | 87 | 4 | 1 | 87 | 2 |
| PA — Panama | Prior | 8,390 | 22 | 6 | 309 | 298 |
| PE — Peru | New | 36,708 | 28 | 15 | 33,926 | 1,419 |
| SV — El Salvador | New | 0 | 0 | 0 | 0 | 0 |

Record rows, named plots and metadata frames are not independent geographic
replicates. The eligible-record and sampled-cell counts in the following mode
tables describe the full mode-specific sampling frame before taxon-specific
training-cell and known-positive background exclusions. Estimable taxa and
contrasts describe the retained within-frame comparisons after those
exclusions.

### Primary: known observation year 2000–2025

The AUC distribution columns below describe **method-metadata-present**
contrasts only. All estimable contrasts belong to that class.
An em dash means no metric is estimable, not AUC zero. Values are displayed to
four decimal places; the JSON receipts retain full numerical precision.

| Country | Eligible records | Sampled cells | Estimable taxa | Contrasts | Median | Q1 | Q3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BR | 49,540 | 8 | 4 | 4 | 0.6250 | 0.2813 | 0.9063 |
| CR, prior | 14,973 | 2 | 6 | 6 | 1.0000 | 1.0000 | 1.0000 |
| EC | 0 | 0 | 0 | 0 | — | — | — |
| GF | 0 | 0 | 0 | 0 | — | — | — |
| GT | 0 | 0 | 0 | 0 | — | — | — |
| HN | 0 | 0 | 0 | 0 | — | — | — |
| NI | 0 | 0 | 0 | 0 | — | — | — |
| PA, prior | 4,613 | 3 | 4 | 4 | 0.0000 | 0.0000 | 0.2500 |
| PE | 2,654 | 2 | 0 | 0 | — | — | — |
| SV | 0 | 0 | 0 | 0 | — | — | — |

Peru's two primary sampled cells occur separately in frames `PE_F001` and
`PE_F015`. Thirteen positive taxon-frame rows belong to the former and three
to the latter, representing 15 distinct taxa in total. Every such row has
one positive cell and no within-frame background cell. Pooling those frames
would create a comparison that the frozen protocol does not authorize.

### Historical/undated descriptive

This table uses the same method-metadata-present class and summary definitions.
It permits unknown years and known years through 2025, including years before
2000. It remains a separate descriptive mode.

| Country | Eligible records | Sampled cells | Estimable taxa | Contrasts | Median | Q1 | Q3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BR | 50,396 | 16 | 6 | 6 | 0.5542 | 0.0938 | 0.8396 |
| CR, prior | 21,326 | 6 | 14 | 25 | 0.6667 | 0.3750 | 1.0000 |
| EC | 2,989 | 17 | 21 | 27 | 0.7500 | 0.4000 | 0.8125 |
| GF | 97 | 1 | 0 | 0 | — | — | — |
| GT | 0 | 0 | 0 | 0 | — | — | — |
| HN | 0 | 0 | 0 | 0 | — | — | — |
| NI | 85 | 2 | 4 | 4 | 1.0000 | 0.7500 | 1.0000 |
| PA, prior | 8,092 | 6 | 14 | 18 | 0.5000 | 0.0625 | 1.0000 |
| PE | 35,289 | 34 | 26 | 53 | 0.5196 | 0.3585 | 0.7250 |
| SV | 0 | 0 | 0 | 0 | — | — | — |

The **method-metadata-missing** class has zero estimable taxa and zero
contrasts, with null median/Q1/Q3, in every country and
mode. This does not mean every observed frame contains method metadata:
Peru's `PE_F002` (RAINFOR 1 ha) is method-metadata-missing, but supplies no
estimable contrast. The two classes have not been pooled.

Within each country and method-metadata class, each estimable taxon's summary
is its equal-weight mean over its estimable frame AUCs. The table's median,
first quartile and third quartile describe those taxon means; quantiles use
linear interpolation at `(n-1)*p`. These summaries include only taxa with an
estimable comparison, whose number is shown explicitly. They do not replace
the full 106-taxon accounting. Scores are not pooled across frames or
countries, and no overall AUC, confidence interval or significance test is
reported. Shared cells, source networks and original training data also mean
that country or frame results are not independent replications.

## 4. All taxa remain in the status denominator

The following totals include all ten countries, retaining the two prior
countries explicitly in the combined evidence. **Every row sums to 1,060**,
and each country contributes exactly 106 entries in each mode.

| Mode | Evaluable exploratory | No eligible positive cells | No within-frame comparison | No match: unknown | Full denominator |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 14 | 62 | 24 | 960 | 1,060 |
| Known-precision | 0 | 100 | 0 | 960 | 1,060 |
| Historical/undated | 85 | 0 | 15 | 960 | 1,060 |

The known-precision mode has zero eligible records and sampled cells in all
ten countries. Every returned record lacks a coordinate-uncertainty
value. This describes missing precision information; it does not establish
that coordinates are inaccurate or that predictive performance is zero.

`NO_MATCH_UNKNOWN` means there is no exact-name focal record in the acquired
country table. `NO_ELIGIBLE_POSITIVE_CELLS` means the taxon matched but no
positive cell survived that mode's exclusions. `NO_WITHIN_FRAME_COMPARISON`
means positive support remains without an estimable within-frame background
contrast. `EVALUABLE_EXPLORATORY` means at least one retained contrast exists.
Unknown or non-estimable results retain null metrics; they are never assigned
zero AUC or interpreted as ecological absence.

### Actual support within estimable contrasts

Ranges refer to retained positive and background cell counts **per estimable
taxon-frame contrast**, not the pooled country sampling frame. The pair-count
columns show the number of contrasts with exactly one positive and one
background cell, followed by the total number of estimable contrasts. All
contrasts in this table belong to the method-metadata-present class.

| Country | Primary positive range | Primary background range | Primary one-pair / all | Historical positive range | Historical background range | Historical one-pair / all |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BR | 1–2 | 1–5 | 1 / 4 | 1–3 | 1–7 | 1 / 6 |
| CR, prior | 1 | 1 | 6 / 6 | 1–2 | 1–3 | 15 / 25 |
| EC | — | — | 0 / 0 | 1–5 | 1–10 | 0 / 27 |
| GF | — | — | 0 / 0 | — | — | 0 / 0 |
| GT | — | — | 0 / 0 | — | — | 0 / 0 |
| HN | — | — | 0 / 0 | — | — | 0 / 0 |
| NI | — | — | 0 / 0 | 1 | 1 | 4 / 4 |
| PA, prior | 1 | 1 | 4 / 4 | 1–2 | 1–2 | 11 / 18 |
| PE | — | — | 0 / 0 | 1–11 | 1–20 | 0 / 53 |
| SV | — | — | 0 / 0 | — | — | 0 / 0 |

Across all ten countries, **11 of 14 primary contrasts** and
**31 of 133 historical contrasts** are one-pair comparisons. Nicaragua's four
historical contrasts all use one positive and one background cell: the AUCs
are 1 for *Clarisia biflora*, *Piper amalago* and *Piper arboreum*, and 0 for
*Ficus tonduzii*. Its median of 1 therefore comes from four extremely small
comparisons, not four independent geographic replications.

For a contrast containing one positive and one background cell, AUC expresses
only the direction of that single ordering, or a tie. A value of 1 does not
establish stable predictive accuracy, and 0 does not mean absence or zero
suitability. More record rows within those same cells do not supply additional
geographic replication.

### The Peru training-overlap exception

The historical/undated evaluation excludes **two positive and six background
taxon-frame events** because their cells occur in the exact original training
union. All are in `PE_F014`, the RAINFOR 0.1 ha Madre de Dios frame. The two
positive exclusions concern *Andira inermis* and *Socratea exorrhiza*. These
are counts summed over taxon-frame evaluations; a shared cell can contribute
more than once, so they must not be described as eight distinct geographic
cells. The reported historical AUCs already apply these exclusions.

All primary training-overlap exclusions are zero, and
all raster-invalid exclusion counts are zero. The nonzero historical Peru
counts are a concrete application of the frozen embargo and must not be
replaced by the prior CR/PA result's zero-overlap statement. Geographic
coordinate exclusions occur earlier and remain separately reported in the
coverage table.

## 5. Datasource identities and remaining bibliography limitations

The [new-country acquisition receipts](neobat/bien_fixed10_20261122/)
and [prior CR/PA acquisition receipt](neobat/bien_external_acquisition_receipt_20261121.json)
identify the following specific datasets. Country lists describe observed
datasource IDs in the full returned
tables, not only sources that produced an estimable focal-taxon contrast.

| BIEN datasource ID | Specific dataset | Countries in full receipts | Direct proximate provider |
| --- | --- | --- | --- |
| 4 | RAINFOR - 1 ha Peru | PE | 391 / SALVIAS |
| 6 | Yanachaga Chimillén National Park | PE | 392 / TEAM |
| 18 | Volcán Barva | CR | 392 / TEAM |
| 19 | Manaus | BR | 392 / TEAM |
| 24 | Cocha Cashu - Manu National Park | PE | 392 / TEAM |
| 27 | Brad Boyle Forest Transects | CR, EC | 391 / SALVIAS |
| 32 | Caxiuanã | BR | 392 / TEAM |
| 37 | La Selva Secondary Forest Plots | CR | 391 / SALVIAS |
| 40 | Gentry Transect Dataset | BR, CR, EC, GF, NI, PA, PE | 391 / SALVIAS |
| 50 | RAINFOR - 0.1 ha Madre de Dios, Peru | PE | 391 / SALVIAS |
| 59 | CTFS Panama Plots | PA | 395 / CTFS |
| 66 | Barro Colorado Nature Monument - Soberania National Park | PA | 392 / TEAM |

All 12 specific dataset rows have null `source_citation` and `doi`
fields. Gentry is the only one with a returned dataset-specific source URL.
The three direct proximate-provider rows supply general SALVIAS (Enquist and
Boyle, 2012), TEAM (Fegraus, 2012) and CTFS–ForestGEO (Anderson-Teixeira et al.,
2015) citations and network websites. The named datasets and these providers
are acknowledged here; their returned bibliography and `acknowledge` access
conditions remain in the receipts. In particular, the two RAINFOR datasets
are linked directly to SALVIAS in the returned database relationships.

These statements describe the returned BIEN bibliography fields. No direct
GBIF datasetKey or DOI crosswalk to the original training observations is
supplied by those specific dataset rows. The expanded lookup improves the
record of source identity but leaves observation-level source independence
unresolved, as in the [prior lineage assessment](NEOBAT_BIEN_CR_PA_SOURCE_LINEAGE_20261121.md).

The acquisition receipts preserve explicitly selected public bibliography,
URL, DOI and access-condition fields for observed datasource IDs and their
direct proximate providers. Method/inclusion free text is represented in the
diagnostic by presence indicators and hashes where necessary; raw site labels
and contact details are not part of this report.

Source names, general network citations and differing titles do not establish
observation-level independence from the original GBIF training download
`10.15468/dl.xwc5zf`. Source independence remains unverified unless a direct
observation/source linkage demonstrates otherwise. Country exclusion and the
cell embargo address the specified geographic training overlap; they do not
prove that BIEN and GBIF originated from different field surveys.

## 6. Execution, preserved evidence and reproducibility

All eight country jobs succeeded in attempt 1 of
[run 44969865714](https://github.com/zuizui0223/esdm/actions/runs/44969865714)
at commit
[`749debe212cbb576ad12ec298073f9ec0883dfdd`](https://github.com/zuizui0223/esdm/commit/749debe212cbb576ad12ec298073f9ec0883dfdd).
The initial [attempt 44969416912](https://github.com/zuizui0223/esdm/actions/runs/44969416912)
failed a pre-query Unicode-normalization test and was replaced before any
BIEN retrieval; it contributes no empirical result. The original CR/PA
evidence comes from [run 44915110088](https://github.com/zuizui0223/esdm/actions/runs/44915110088)
and is described in the [prior result memo](NEOBAT_BIEN_EXTERNAL_PLANT_RESULT_20261121.md).

The [combined summary](neobat/bien_fixed10_summary_20261122.json) validates all
1,060 original positive/background training-count records against the frozen
106-by-17 original receipt, all country/taxon/mode memberships, completed fit
counts, acquisition/result count agreement and descriptive summaries. Each
diagnostic also records the adapter's exact training-cell membership replay.
The summary identifies the 848 new fits and 212 prior fits separately; it does
not imply that all 1,060 models were newly fitted in this execution.

The [artifact provenance manifest](neobat/bien_fixed10_artifact_provenance_20261122.json)
records the eight successful job IDs, eight artifact IDs and ZIP hashes, and
the filenames, byte counts, SHA-256 hashes and Git blob hashes of all **16 new
public JSON files**. The acquisition and diagnostic files in the
[country receipt directory](neobat/bien_fixed10_20261122/) preserve their exact
downloaded artifact-member bytes. The manifest also verifies that the two
prior CR/PA files remain byte-for-byte unchanged:
[acquisition](neobat/bien_external_acquisition_receipt_20261121.json) and
[diagnostic](neobat/bien_external_plant_diagnostic_20261121.json).

| Preserved evidence | SHA-256 |
| --- | --- |
| Frozen ten-country extension specification | `241c6ce6a1cf274553a078f551bb5c1b1623a7e73fbf8be683bab2f0359ee765` |
| Combined ten-country summary | `b1edfc4d6dfce2bfc9642b619bddd0f9471d80e22ec790fec7c20b4a3edf9ee0` |
| Artifact provenance manifest | `873021d52dcfae013e67f3d4b52f498a7a760a7b6061b763d7d6353c2089d36f` |
| Unchanged prior CR/PA acquisition | `1a1635c23f3100d9794a55eb3f56bf96b5f5285cfffe5e97db114acee9053863` |
| Unchanged prior CR/PA diagnostic | `fa8342ab203152b8ec347653961612142b19a9e44ca20864904b540e7ed1f788` |

All acquisitions report BIEN R package **1.2.8**, database **4.2.8**, and
database release date **2023-06-27**. An earlier numeric `db_release_date`
value of `19535` represents this R Date. All new and reused diagnostics
record NumPy 2.2.6, scikit-learn 1.7.2, rasterio 1.4.3 and pyproj 3.7.2,
matching the four original numerical pins; they also record SciPy 1.18.1.

The original plant archive SHA-256 remains
`4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`.
The unchanged roster SHA-256 is
`41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`.
The raster and original-helper hashes, full training counts and numerical
package versions are recorded in the diagnostic receipts.

A completed zero-row country query with the required schema is distinct from
an exception, timeout or malformed response. The former retains all 106 taxa
as unknown with null metrics; the latter is an operational failure and cannot
be silently converted into an empty biological result.
Guatemala, Honduras and El Salvador are actual completed, schema-valid
zero-row queries in the preserved evidence. Each still has 106 completed
original model fits and 106 unknown taxon results in every mode.

Only aggregate acquisition receipts, aggregate diagnostic results, the
combined summary and preservation metadata are public. Raw records,
coordinates, plot/cell identifiers, fitted coefficients and individual
predictions are not published. Temporary source tables and archives are
removed after each job. Preserved artifact members retain their exact original
bytes, including the previously opened CR/PA files.
