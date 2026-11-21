# NeoBat exploratory v2 fixed 106-plant input-universe freeze

Date: 2026-11-19. Status: **EXPLORATORY alternative**, not the frozen 255-plant v1 model or independent biological validation. Main stays unchanged.

## Why v2 exists

The original v1 contract requires fitting source-independent plant suitability for all 255 candidate plant names in each of 17 country holdouts. From original DOI-verified source QC (no bat heldout rankings), only 106/255 plants have >=20 known-precision 25km occurrence cells **outside every one of those 17 holdout countries**. Strictly independent training for the other 149 plants is not supported under this frozen source-quality denominator. Silently setting their relative suitability to 0 would be erroneous. This is an input-identifiability problem and not biological evidence against fruit-resource tracking.

## One pre-registered source-only alternative test

1. Keep the original 84 bat×country roster **as the accounting denominator**, and derive a **single intersection** plant universe: all 255 initially frozen plants for which outside-country known-precision 25km recorded-cell count is >=20 for *every one of the 17 fixed countries*. Expected size is exactly **106** from the published source-only trainability receipt; derive and cryptographically hash the sorted species names to prevent later edits.
2. Re-download the author-origin pinned **NeoBat original RECORDS and SITES only**, with original Git object hashes verified. Do NOT download new GBIF occurrences or infer diet from GBIF co-observation. Exclude each heldout country's **entire** NeoBat site-publication reference embargo, not only direct fruit records.
3. Per frozen bat×country pair, count true source-listed **frugivory, frugivore-guild** partner plant names that fall in the fixed 106 and independently have >=5 known-precision recorded cells in the heldout country. Report the number of distinct outcountry source refs supporting retained partners.
4. Declare an exploratory v2 **input-qualified** pair when >=3 such partner species and >=2 original source refs survive. Do not tune thresholds using source co-location results or heldout bat scores.
5. For the 106-plant, source-embargoed bipartite network, test whether a degree-preserving 2-edge swap can change the focal bat's partner identities **without adding duplicates**. Report `N1_focal_swap_possible`, and the number of surviving pairs; do not interpret this as statistical N1 power or a heldout null effect.
6. Keep and report **every one of the 84** original pairs, including new v2 source-gate failures. Do not re-select or drop negative source-co-recording folds from the separate same-cell source audit.
7. This is **source-only, no bat heldout response opened in this run, no plant SDM fitted and no M3−M1/N1 rank AUC**. An eventual ecological v2 would require independent WorldClim/climate, forest, topography, target-group effort and country-crossfitted plant models plus genuinely heldout response ranking. All conclusions on the same GBIF source remain exploratory.

The v1 255-plant contract and primary inferential claims stay frozen and not estimated. No protected animal coordinates, spatial cells, occurrence IDs, or species×cell tables may be committed.
