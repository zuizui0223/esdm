# NeoBat: CR/PA plot sources and the recovered original GBIF registry

Date: 2026-11-21. Scope: the already opened Costa Rica and Panama BIEN pilots,
the frozen 106 focal plants, and the original GBIF plant download. No new
country, taxon roster, model, or eligibility threshold is introduced.

## Result

The BIEN return contains **seven country-by-source groups, representing six
distinct BIEN dataset labels/IDs and three proximate providers**. The original
GBIF source-key list has now been recovered from the **exact frozen ZIP**;
all **1,202 keys and their individual record counts** agree with GBIF's
download-specific dataset metadata. This resolves the missing source-registry
problem. It does **not** establish that the BIEN field observations are
independent of the original GBIF observations.

## 1. Observed BIEN source composition

These are the original returned labels. Records are matched plant-record rows;
plot counts use datasource + dataset + plot_name, not verified independent
geographic or statistical units. Taxon counts overlap between source groups.

| Country | Proximate provider label | Dataset label | BIEN datasource_id | Matched rows | Matched taxa | Nested plot labels |
|---|---|---|---:|---:|---:|---:|
| CR | SALVIAS | Brad Boyle Forest Transects | 27 | 29 | 4 | 8 |
| CR | SALVIAS | Gentry Transect Dataset | 40 | 17 | 10 | 3 |
| CR | SALVIAS | La Selva Secondary Forest Plots | 37 | 78 | 11 | 14 |
| CR | TEAM | Volcán Barva | 18 | 433 | 7 | 6 |
| PA | CTFS | CTFS Panama Plots | 59 | 304 | 22 | 27 |
| PA | SALVIAS | Gentry Transect Dataset | 40 | 28 | 7 | 2 |
| PA | TEAM | Barro Colorado Nature Monument - Soberania National Park | 66 | 642 | 9 | 6 |

The group sums reproduce **CR: 557 rows / 31 plot labels** and **PA: 974 rows /
35 plot labels**, with **17 and 22 distinct matched taxa**, respectively.
All seven groups have complete source labels and IDs; no matched source label
or ID is missing. Their 24-taxon union and 15 shared taxa remain as reported in
[the first evidence memo](NEOBAT_BIEN_CR_PA_FIRST_PLOT_EVIDENCE_20261121.md).

Gentry is the same BIEN dataset ID in both countries. Its two country subsets
must not be represented as two independently provided source datasets. This
does not, by itself, establish duplicated observations between countries.
TEAM contributes 1,075 of 1,531 matched record rows (70.22%); that concentration
is a property of record counts, not a fruit-resource quantity.

The [official BIEN contributor table](https://bien.nceas.ucsb.edu/bien/data-contributors/all/)
corroborates these six dataset names and the SALVIAS/TEAM/CTFS ingestion routes.
This establishes how BIEN received them, not whether the same original
observations also reached GBIF through another route.

### Untouched BIEN receipts and acquisition provenance

- [CR receipt](neobat/bien_cr_source_registry_20261121.json)
- [PA receipt](neobat/bien_pa_source_registry_20261121.json)
- Original successful [run 44901574425](https://github.com/zuizui0223/esdm/actions/runs/44901574425),
  executed head `51dc8bd914a6dcac02cb5b7e733b9e42e9fc5920`.
- BIEN database version/build: `4.2.8` / `19535`. Both queries used
  `all.metadata=TRUE`, `natives.only=TRUE`, and `cultivated=FALSE`.
- The two JSON files above preserve the artifact member bytes without adding
  or changing fields. Both successful receipt statuses were inspected; the
  workflow's success status alone was not used as evidence of source success.

| Country | Artifact ID | ZIP SHA-256 | Original JSON SHA-256 |
|---|---:|---|---|
| CR | 14706576560 | `23055b81dfff4de03a229be0e9cc08af33905edc4be799760a6bc17053860386` | `84c2261a19ed8e5a40166add550a0a0c95c8d73da97775e7ed72875ce8c3f066` |
| PA | 14705959029 | `23283723eb43f50ae244db78c88a93af26ad9502ebaa7cced8d98ccdcf750cfa` | `60892d395e531df9b63e4920909a09ba08513759f980c6ed22374e59a5524a7d` |

## 2. Recovered original GBIF source membership

Original plant download: [DOI 10.15468/dl.xwc5zf](https://doi.org/10.15468/dl.xwc5zf),
download key `0001157-261118162104854`. The existing archive was downloaded;
no new GBIF download request was submitted.

- ZIP bytes: **39,741,309**.
- ZIP SHA-256: `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`.
- Source: **367,988 records / 1,202 datasetKeys** across the original 29-country,
  2000–2025 query scope. The original accepted-name query contains **255 plants**;
  this must not be confused with the **106 focal plants**.
- Frozen focal roster SHA-256:
  `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`.
- All keys and per-key record counts were checked against the
  [download-specific dataset registry](https://api.gbif.org/v1/occurrence/download/0001157-261118162104854/datasets).
  Dataset titles and DOIs are metadata retrieved at the UTC timestamp recorded
  in the saved JSON; record membership is anchored to the frozen ZIP.

| Scope | Original source rows | Original source keys | Strict original-255 rows | Strict original-255 keys | Strict focal-106 rows | Strict focal-106 keys |
|---|---:|---:|---:|---:|---:|---:|
| All 29 countries | 367,988 | 1,202 | 89,718 | 242 | 81,882 | 235 |
| CR | 16,189 | 56 | 5,351 | 12 | 4,900 | 11 |
| PA | 5,262 | 35 | 3,331 | 7 | 3,222 | 7 |

The CR/PA raw-source union is **67 datasetKeys**. Strict screening replays the
original accepted speciesKey mapping, GBIF-ID deduplication, country/year
scope, valid finite coordinates, and known finite coordinate uncertainty
between 0 and 12,500 m inclusive. The strict original-255 total reproduces the
original full-QC count of 89,718 exactly; the focal-106 screen adds roster
membership only.

**These are occurrence-row counts, not 25 km cell counts or final model
training/test counts.** Raster masks, source-matched background subtraction,
holdout embargoes, and final fitted-model retention are not reconstructed here.

Saved evidence:

- [CR/PA registry with full provenance and method](neobat/original_plant_gbif_CR_PA_source_registry_20261121.json)
- [All 1,202 original dataset keys, titles, DOIs, and counts](neobat/original_plant_gbif_all1202_dataset_registry_20261121.csv)

## 3. What the comparison establishes

An exact comparison of the six BIEN dataset labels against all 1,202 GBIF
dataset titles, after Unicode NFKC normalization, case folding, and whitespace
normalization, finds **zero title matches**. This is only an alias-screening
result. It cannot detect publication under a different title, collection,
institution, aggregator, or record identifier and is **not proof of disjointness**.

Three related institutional datasets do occur in the frozen raw GBIF source:

| GBIF dataset | datasetKey | Raw rows, all 29 | Raw CR | Raw PA | Strict original-255 rows, all 29 |
|---|---|---:|---:|---:|---:|
| Tropicos MO Specimen Data | `7bd65a7a-f762-11e1-a439-00145eb45e9a` | 9,247 | 948 | 158 | 0 |
| Tropicos Specimens Non-MO | `e053ff53-c156-4e2e-b9b5-4462e9625424` | 11,974 | 724 | 80 | 0 |
| NMNH Extant Specimen Records (USNM, US) | `821cc27a-e3bb-4bc5-ac34-89ada245069d` | 863 | 20 | 20 | 0 |

These institutions are useful provenance leads, but their collection names
do not identify them as the publisher of the observed BIEN plot rows. The
[primary SALVIAS report](https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00086&lang=en)
links its standardized Gentry data to the
[original Missouri Botanical Garden transects](https://www.mobot.org/MOBOT/research/gentry/transect.shtml).
That connection must not be replaced by an unsupported equivalence between
Gentry plot data and Tropicos specimen data.

No direct mapping from the six BIEN IDs to GBIF datasetKeys or shared
observation identifiers was verified. A local, read-only attempt to access
the published BIEN datasource registry failed at DNS resolution before
connecting. The [official RBIEN citation helper](https://github.com/bmaitner/RBIEN/blob/master/R/BIEN.R) documents lookup by
`datasource_id` and `proximate_provider_datasource_id`; those source-row
citations/URLs, followed where necessary by original observation identifiers,
are the remaining concrete evidence needed for source-equivalence assessment.

For all six observed BIEN source datasets, the present independence assessment
therefore remains **UNVERIFIED**, rather than overlapped or disjoint. Absence,
fruit biomass, ripe-fruit availability, and bat-model performance are not
inferred. The earlier descriptive plot-count thresholds are not promoted to
model eligibility criteria.

## 4. Reproduction and validation

The [stdlib extraction script](../../scripts/neobat_gbif_cr_pa_source_registry.py)
supports Python 3.10+. It accepts an existing local copy of the original ZIP
and verifies its SHA-256 before processing. By default it fetches five frozen
input receipts at immutable design commit
`d65817fcb3c39060ed544261c291d76a198299c6`, checks their Git blob hashes, and
recomputes the frozen106 roster hash. `--input-dir` can instead supply those
exact receipts locally.

```bash
python -O scripts/neobat_gbif_cr_pa_source_registry.py \
  --archive /path/to/0001157-261118162104854.zip \
  --output-dir build/neobat/source_registry
```

The script writes dataset-level JSON/CSV aggregates only. Occurrence rows,
coordinates, occurrence IDs, and cell IDs are not written. Validation uses
explicit exceptions and remains active under `python -O`.

The end-to-end extraction was run successfully, independently rerun from the
immutable remote receipts, and reviewed against the original archive. The
all-1,202 CSV was byte-identical between the two runs; the JSON differed only
in its retrieval timestamp. All 67 CR/PA registry rows agreed with independent
reconstruction. The two BIEN ZIP digests, original JSON bytes, successful
receipt statuses, and group count sums were also verified.
