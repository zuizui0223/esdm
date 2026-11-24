# NeoBat 106×17 global GBIF datasetKey embargo: empirical source-independence ceiling

Date: 2026-11-19. Original data reopening was performed under the already committed
`docs/replication/NEOBAT_BOTANICAL_GLOBAL_DATASETKEY_EMBARGO_FROZEN_20261119.md`,
after source-free tests and before any new source-ID result was inspected.

## Reproducible execution

- Synthetic source-embargo regression: [Actions #44541369075](https://github.com/zuizui0223/esdm/actions/runs/44541369075) **PASS**.
- Original source-only archive rerun: [Actions #44541504093](https://github.com/zuizui0223/esdm/actions/runs/44541504093) **PASS**, source and original all **1,802** plant×country prior source-matching counts reproduced exactly. No GBIF download POST, plant SDM fit, bat AUC or raw source IDs/coordinates committed.
- Full receipt: `docs/replication/neobat/plant_106x17_global_source_embargo.json`; compact receipt: `docs/replication/neobat/plant_106x17_global_source_embargo_compact.json`.
- Original GBIF plant download DOI `10.15468/dl.xwc5zf` and source ZIP SHA `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b` reverified. 367,988 rows in original year and country frame, 1,202 distinct nonblank GBIF datasets overall.

## Fixed 106-plant global source-disjoint feasibility (not a rank AUC)

| Input source-quantity criterion | Country withheld, identical dataset may be reused across borders | All botanical `datasetKey` used in withheld country excluded from entire outside-country training |
|---|---:|---:|
| Trainable plant × withheld-country pairs | **1,802 / 1,802** | **1,233 / 1,802** |
| Adequate outcountry training **and** within-country scoring source quantities | **677 / 1,802** | **497 / 1,802** |
| Plant taxa trainable for **all** original 17-country folds | **106 / 106** | **35 / 106** |
| Original 17 countries with complete fixed 106-plant training pool | **17 / 17** | **0 / 17** |

Source disjointness from identical GBIF dataset IDs is a stronger **input-identifiability** requirement; it is NOT proof of truly independent botanical surveys, institutions, publishing organizations or ecological abundance. Importantly, the postembargo 497 source-qualified pairs are **not 497 fitted AUCs**: raster nodata, positive/background data and final ecological checks may further reduce them.

Examples of source loss:

- Colombia original source datasets: 706 IDs, only 41 appear in other original 29 source countries. Yet the full-source embargo reduces plants trainable for Colombia from **106 to 53**; a small number of wide-ranging datasets may contribute many outcountry training records. Source input test eligible: **90 to 49**.
- Mexico: original 106 trainable **to 55**; source-input test eligible **73 to 41**.
- Brazil: trainable **106 to 78**; test eligible **65 to 48**.
- All 17 countries retain **at least one** source-disjoint test-eligible plant, but zero countries retain the full 106.

The previously fixed three Colombia pilot sentinels remain **source-quantity eligible** after embargo: *Cecropia obtusifolia* 37 outside-country focal training cells / 574 background, *Ficus insipida* 103/670, *Piper aduncum* 68/659. These numbers are before the previous same-cell other-taxon symmetry and WorldClim nodata filters and are **not ecological model performance**.

## Decision

**The claim that the 106-plant universe can be fully crossfitted across all 17 original countries does not survive a stricter same-GBIF-dataset independence rule.** A putative full 106-species linked-resource M3 therefore still cannot be promoted as a source-independent ecological SDM. The original v1 255-plant primary contract remains frozen and unestimated.

A scientifically constrained next *exploratory* step is a **paired Colombia three-sentinel** source-disjoint refit, using the **same heldout source-record population**, original climate/elevation source and fixed regression; report all three species, paired AUC changes and stops. No selective change to the original country or three sentinels.

The original source was already opened; no results here constitute independent external replication or actual fruit availability.
