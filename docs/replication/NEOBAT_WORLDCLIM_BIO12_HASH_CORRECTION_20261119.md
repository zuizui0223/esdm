# NeoBat WorldClim BIO12 frozen-member hash correction (2026-11-19)

**Scope: technical source-integrity correction only. No bat or plant responses used.**

## Evidence

- URL: `https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip`
- ZIP SHA-256 independently verified in the first source check and member forensic:
  `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf`
- Member: `wc2.1_10m_bio_12.tif`, uncompressed 1,963,655 bytes.
- Old manually pinned BIO12 member hash (failed): `1e823e951ace0186c6eadd7368b4d0385f8c51cc952282c0f2d640bf7790fea5`.
- Observed member SHA-256 from **the same archive with correct ZIP SHA-256**:
  `1e823e951ace0186c6eadd7368b4d0385c8f51cc952282c0f2d640bf7790fea5`.
- Two nibbles at positions 34 and 36 (1-based) were transposed in the manual pin: observed `...4d0385c8f51...`, old `...4d0385f8c51...`.
- Original diagnosis: `docs/replication/neobat/worldclim_bio1_bio12_source_preflight.json` status `WORLDCLIM_SOURCE_STOP`, due to `WORLDCLIM_FROZEN_BIO12_MISMATCH`.
- Independent member-hash evidence: `docs/replication/neobat/worldclim_member_hash_diagnostic.json`, status `INNER_MEMBER_HASH_DIAGNOSTIC_ONLY`.

## Correction rule

The source ZIP's identity and URL must remain frozen. Replace only the erroneous
BIO12 member SHA-256 constant in the source preflight; **do not** modify
the raster, resample it, modify its values, shift source versions, or touch
bat/plant ecological outcomes.

Then run a **new** source-only GeoTIFF metadata inspection with the corrected
member pin and assert: original ZIP SHA unchanged, BIO1/BIO12 unique, both
raster bands are single-band, EPSG:4326, correct dimensions and nodata.
If any fail, report a terminal `WORLDCLIM_SOURCE_STOP` and do not fit SDM.

WorldClim v2.1 10 arc-minute bioclimatic surfaces summarize 1970–2000.
The temporal discrepancy with the 2000–2025 GBIF occurrence window must
be stated in every model as a **long-term climate baseline**, not annual
feeding/resource conditions. Additional forest structure, source effort,
target-group background and independently cross-fitted plant models
are required before any M1-vs-M3 comparison.
