# BIEN external plant diagnostic: prelisted ten-country extension

Frozen on 2026-11-22 (Asia/Tokyo), before retrieving or scoring the eight new
country tables. This is an exploratory follow-up to the completed CR/PA
diagnostic, whose geographic support was too small for reliable accuracy claims.

## Scope fixed from the existing manifest

Use the existing
[`NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json`](NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json)
without changing its 106 plants or its ten prelisted shadow-fitted countries:
**BR, CR, EC, GF, GT, HN, NI, PA, PE, SV**. These countries were listed before
the CR/PA outcomes. All ten have 106 original country-excluded training-count
records at immutable design commit
`d65817fcb3c39060ed544261c291d76a198299c6`.

New acquisitions and fits cover every remaining country: **BR, EC, GF, GT, HN,
NI, PE, SV**. No country is selected or dropped using match counts, sampled
cells or AUC. The existing CR/PA result bytes from run `44915110088` remain
unchanged and are reused explicitly as previously opened results.

The combined denominator is **106 plants x 10 countries = 1,060 taxon-country
entries in each mode**. The new run fits 848 original specifications; the 212
CR/PA fits are supplied by their preserved prior run. This is not 1,060 newly
fitted models, and the combined panel is not a new confirmatory test.

## Comparison rules remain unchanged

Reuse the
[original comparison specification](NEOBAT_BIEN_EXTERNAL_PLANT_DIAGNOSTIC_FROZEN_20261121.md)
and PR #277 grouping/metric implementation. Only the requested country scope,
source metadata collection, execution and aggregate reporting are extended.

- Full native-only country tables through official
  `BIEN_plot_country(all.metadata=TRUE, natives.only=TRUE, cultivated=FALSE)`;
  include plots with no focal-plant match in the sampling background.
- Exact fixed-name matching, original 25 km EPSG:6933 cells and original
  SHA-verified climate rasters. No new taxonomic reconciliation or resolution.
- Source/method/area/inclusion metadata frames; missing metadata stays explicit.
  Equal metadata does not establish equal effort.
- Deduplicate record/stem/plot/visit support to focal-taxon cells within frames.
  Censor every known focal-positive cell from background across country-level
  frames and date modes. Remove each taxon's exact original training-cell union.
- The original plant model, original training selection, numerical pins and
  all training-count checks remain fixed. Complete all requested country fits
  before accepting that job's BIEN cells for prediction. No BIEN fitting or
  tuning, bat outcomes, ecological M3, occupancy or fruit-resource estimation.
- Preserve the same three modes: `primary_2000_2025`,
  `known_precision_2000_2025`, and `historical_undated_descriptive`. Unknown
  uncertainty remains disclosed in the first and third; the second requires
  known uncertainty <=12,500 m. Do not infer dates or precision from citations.
- AUC is the within-frame positive-versus-background pair concordance, with
  ties at 0.5, requiring at least one cell in each class. Keep all unknown,
  ineligible and non-comparable taxa. No minimum-plot filter is introduced.
- Retain separate equal-weight frame means for method-metadata-present and
  method-metadata-missing frames. Frames can share cells and are not independent
  replicates. Background does not mean ecological absence.

## Empty responses, failures and provenance

A successfully returned zero-row country table with the required schema is an
observed lack of available BIEN plot records, not a species absence. Preserve
all 106 taxa with unknown statuses and null metrics. An exception, timeout,
wrong-country return, malformed schema or incomplete query is an operational
failure; never convert it into a successful empty table. Keep the prelisted
country in the accounting and resolve the operational failure before declaring
the combined execution complete.

Record actual database/package versions and complete-table row counts. Retrieve
public bibliography fields for observed datasource IDs and their direct
proximate providers. Source citations or URLs may enable further source identity
assessment, but missing identifiers or differing titles do not establish
independence from the original GBIF observations. This follows the same
exploratory source-independence limitation as CR/PA.

## Predeclared descriptive summaries

For every country and every mode, report records, sampled cells, matched taxa,
the full four-status count table, and estimable taxon-frame contrasts. Report
positive/background cell-count ranges for the actual estimable contrasts, so
one-pair AUCs remain visible.

For each method-metadata class separately, summarize the distribution of the
existing per-taxon equal-frame-mean AUCs using the number of estimable taxa,
median, first and third quartiles. Quantiles use linear interpolation at
`(n-1)*p` in the sorted values; no estimable values gives null summaries.
These describe only the taxa with observed comparisons, whose denominator is
always shown. They do not replace the 106-taxon status accounting.

Do not pool raw scores across frames or countries, report a pooled overall AUC,
calculate p-values/confidence intervals, impose success thresholds or select
well-performing taxa. Models share training data and taxa, so country results
are not assumed to be independent statistical replicates. The eight new country
results and previously opened CR/PA results remain identifiable in the summary.

## Output and verification

Publish only aggregate acquisition receipts, aggregate diagnostic results,
combined summaries and interpretation. No raw tables, coordinates, plot/cell
identifiers, individual predictions, coefficients or private source archives
are uploaded. Private tables are temporary job inputs and are removed after
the job. Preserve the exact downloaded public artifact member bytes.

Verification covers unchanged metric semantics, default CR/PA compatibility,
the fixed ten-country boundary, valid empty-country accounting, source metadata
selection, and all 1,060 unique result pairs per mode. Inspect every actual
country receipt and model count; workflow success alone is insufficient. One
whole-change independent review and exact-final-head repository CI precede
integration. Do not add successive eligibility gates or rerun unchanged
analyses merely to obtain a favorable result.
