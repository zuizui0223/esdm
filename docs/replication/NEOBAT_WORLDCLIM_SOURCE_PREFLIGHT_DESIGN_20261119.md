# NeoBat 2D SDM climate raster source preflight (2026-11-19)

This is a **predictor-source authenticity/geometry test only**. No GBIF bat or plant occurrence rows are opened, no plant SDM or heldout response is fit, and no climate coefficient is estimated.

Reuse the same frozen WorldClim v2.1 10-arc-minute bioclimatic archive successfully validated in `esdm` E2 on 2026-09-27 (`docs/replication/E2_MICA_WORLDCLIM_FROZEN.json`):

- URL: `https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip`
- Original archive SHA256: `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf`
- BIO12 raster: `wc2.1_10m_bio_12.tif`, source SHA256 `1e823e951ace0186c6eadd7368b4d0385f8c51cc952282c0f2d640bf7790fea5`.
- BIO1 raster: `wc2.1_10m_bio_1.tif`; its new source digest and GDAL/GeoTIFF metadata must be recorded before use.
- Provider metadata: WorldClim 2.1 historical reference period **1970–2000**; this is a long-term climate normal older than GBIF bat/plant occurrence dates 2000–2025. Never label it contemporary year-specific weather or directly estimate climate-change trends.
- Read only these two GeoTIFFs' source digest, CRS, dimensions, affine transform, nodata, band count, raster scales/offsets and band tags. Do NOT inspect biological occurrence response values at this gate.
- No model promotion until forest structure/cover, terrain and target-group observer effort have independently sourced, compatible covariates, and environmental sampling uses the fixed 25-km equal-area cell geometry without test-response leakage.
- No climate raster binary is committed to GitHub; a source checksum/geometry-only receipt is retained.
