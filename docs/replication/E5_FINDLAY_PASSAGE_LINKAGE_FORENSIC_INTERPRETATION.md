# E5 Findlay: identity-forensic audit of the two CCTV data tables

**Separate post-outcome exploratory result:** `ROW_ORDER_AGREEMENT_NO_PASS_ID`.

A one-shot source audit, [run 38351094780](https://github.com/zuizui0223/esdm/actions/runs/38351094780), compared the two **exact Git-blob-pinned** Findlay FOX/BADGER files. The original response analyses and thresholds were not rerun or refit. The audit was planned after published qualitative direction and prior aggregate results were already exposed, so this is not an untouched preregistration.

## What the source tables actually show

Both the trigger and registration tables contain **881 records**.

Under the fixed shared nonresponse signature of `SPECIES`, `CT.POS`, `ORIENT`, `DIST`, `LOIT` and `AIR`:

- **881 of 881** row-order positions have identical shared signatures.
- **881 of 881** row-order positions also have identical `TRIGGER` flags.
- There are **530** fingerprint configurations represented by exactly one record in each table.
- The remaining **351** rows belong to duplicated, ambiguous fingerprint configurations.
- Zero unmatched fingerprint rows were found in either table.
- **None** of the predeclared explicit per-passage ID field names was shared in the source files.

This is strong empirical evidence that both released files were exported from *consistently ordered versions of the same passage-level observational record set*. It materially supports the comparability assumption underlying the **descriptive** FOX composite more than mere matching totals (55 near triggers and 47 far triggers) could have done alone.

It does **not** establish an independently verified, one-to-one passage identity for all 881 rows: identical covariate signatures are not unique for 351 rows, and row position is not a documented unique passage identifier. An unlisted unconventional identifier or an author-provided event crosswalk has not been ruled out.

## What this does—and does not—change

The original frozen FOX rates remain a **descriptive** stage calculation: close (`<=1m`) trigger 55/88, registration 19/55; far (`>3m`) trigger 47/175, registration 27/47. Their composite per-pass rates remain 19/88 versus 27/175 *conditional on proper source passage correspondence*. The new 881-row order consistency makes that correspondence more plausible, without proving it through immutable per-pass IDs.

The aggregate post-outcome \`k\`-substitution sensitivity record remains valid **as a hypothetical stress test**, but the observed number or bound of linkage mismatches `k` remains unknown. The k=4 (composite reversal) and k=6 (registration reversal) thresholds have **not** been observed. The BADGER far 16-versus-15 eligible-trigger count discrepancy is not repaired or attributed to a specific passage.

**No original Findlay result was reclassified.** No new biological response rate, ecological transfer performance, causality, confidence interval, diel correction, E5 G4 pass or qualified candidate is claimed. Original standard E5 remains **0/17 qualified**; wild-pig UNRESOLVED/QC HOLD and Rhode Island's G4 hard stop remain unchanged.

The next decisive external evidence would be a published source-field codebook/creator confirmation establishing a unique passage ID across both files (or original CCTV annotation with a persistent passage key). It should not be fabricated from row position alone.

Evidence identifiers are frozen in `E5_FINDLAY_PASSAGE_LINKAGE_FORENSIC_RECEIPT.json`.
