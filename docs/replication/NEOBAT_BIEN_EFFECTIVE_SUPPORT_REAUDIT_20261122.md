# NeoBat BIEN ten-country panel: effective-cell support re-audit

Date: 2026-11-22 (Asia/Tokyo). **Post-hoc descriptive analysis of previously fixed, already-scored public aggregate receipts.** No data were queried, no plant model was refitted, no taxon/country was selected by outcome, and no original AUC or denominator was changed.

## What changed in interpretation

The [ten-country BIEN result](NEOBAT_BIEN_FIXED10_EXTERNAL_RESULT_20261122.md) retained 106 plants in ten prelisted countries and distinguished three date/coordinate-precision modes. It reported 14 estimable **primary** taxon-frame contrasts and 133 estimable **historical/undated** contrasts. This re-audit makes their *effective cell support* and shared source dependence explicit, using the actual retained positive and background cell counts next to each frozen frame AUC.

**The apparent descriptive AUC advantage does not persist when comparing contrasts containing multiple cells on both sides.** This is not a new significance test and does not establish that the model performs worse than chance; it is a sensitivity of a selected descriptive subset and its very limited independent support.

| Minimum retained cells in each class, per taxon-frame | Primary contrasts | Historical/undated contrasts | Historical/undated median AUC, over contrasts | Distinct historical countries | Distinct historical country-frames | Distinct historical source datasets |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 14 | 133 | 0.6250 | 6 | 17 | 10 |
| 2 | 2 | 41 | 0.4815 | 3 | 6 | 4 |
| 3 | 0 | 26 | 0.4677 | 3 | 5 | 3 |
| 5 | 0 | 5 | 0.6333 | 2 | 2 | 1 |

At one cell per class, the primary has 11 one-positive/one-background contrasts among 14. Historical/undated has 31 among 133. The strict known-coordinate-precision mode has zero contrasts at every cell-support level, because all BIEN rows lack a reported coordinate uncertainty. Zero means **not estimable** here, not absence or zero predictive performance.

These are unweighted **frame-contrast AUC medians**, not the per-taxon equal-frame-mean AUC medians used in the original country tables. They are deliberately not pooled performance estimators. Contrasts share cells, taxa, metadata frames, training observations and source networks, and the value of a country-frame or dataset count must not be mistaken for an independent sample size.

## Source concentration and direction

At >=3 positive and >=3 background cells, only **26 historical contrasts** remain, from **16 unique plant taxa**, **3 countries (BR 1, EC 5, PE 20)**, **5 country-frames** and **3 specific source datasets**. Among these 26 AUCs, **11 are above 0.5 and 15 below 0.5** (none equal). The unweighted contrast mean is 0.4688 and median 0.4677. Those comparisons are *not* 26 independent replications.

At >=5 cells in both classes, the remaining **five** historical comparisons come from **two country-frames, Ecuador and Peru**, but all five belong to the **same Gentry Transect Dataset** (BIEN datasource ID 40). Their AUCs span **0.4400 to 0.7889**, with median 0.6333. This does not demonstrate transfer across independent vegetation source datasets or repeated confirmation in five separate study systems.

At >=2 cells in each class, the 41 historical contrasts have median 0.4815 and mean 0.4776. They are concentrated in three countries and six frames. The result changes sign around 0.5 as the reporting support changes: it is inappropriate to quote the 133-contrast median 0.625 as robust external prediction.

## Inferential ceiling and immediate consequence

1. **Do not promote the 106-plant climate-only shadow to ecological M3.** There is no estimate of bat-model gain, observed fruit biomass, fruit availability, plant occupancy or a trophic mechanism in this audit.
2. **Do not interpret BIEN and GBIF as observation-independent.** [The original source lineage review](NEOBAT_BIEN_CR_PA_SOURCE_LINEAGE_20261121.md) recovered original GBIF dataset keys, but no observation-level BIEN→GBIF origin linkage; different dataset titles alone cannot prove disjointness.
3. **Do not expand or retune BIEN after seeing these values.** Further BIEN-country queries and new pass/fail cell gates would enlarge a post-hoc search. Freeze this descriptive result with nulls and all 106×10 statuses.
4. For a new biological result, prioritize a truly separately documented field resource/vegetation dataset with original primary data identifiers and bat outcomes, then a *new, prospective* M3-vs-M1 comparison. Existing tree/plot stems remain a weak resource proxy; fruiting and seed rain require their own observations.

This re-audit introduces **no new eligibility rule**. The levels 1, 2, 3 and 5 are multiple transparent reporting lenses over the same fixed scores, not grounds to label any subset a new success or failure. No p-values, confidence intervals, pooled cross-frame AUC, cross-dataset independence assertion or test-optimized threshold is used.

## Reproduction and integrity

Run `python -m scripts.neobat_bien_support_reaudit --repo-root .` from the repository root. The script reads only the preserved aggregate receipt files in `docs/replication/neobat/`, checks the original CR/PA SHA-256 and each of the eight new country JSON SHA-256 values against the committed [artifact provenance](neobat/bien_fixed10_artifact_provenance_20261122.json), retains 106 species in every country and mode, rejects altered AUCs or changed score counts, and computes the support table without accessing raw locations or individual predictions. The tests include a replay against all ten committed country receipts, an altered score and a missing taxon.

Source: [combined fixed panel](neobat/bien_fixed10_summary_20261122.json), [unaltered country receipts](neobat/bien_fixed10_20261122/), and [prior Costa Rica/Panama diagnostic](neobat/bien_external_plant_diagnostic_20261121.json).
