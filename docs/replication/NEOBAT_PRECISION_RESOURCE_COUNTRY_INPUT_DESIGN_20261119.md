# NeoBat precision-conditioned resource-input geography v1 — exploratory design

Date: 2026-11-19. **Status: source-denominator analysis only; not a bat SDM or confirmatory ecological result.**

Source full DOI GBIF audit has been opened for 26 bats and 255 plants; this is **not sealed validation**. The next diagnostic checks whether a given potential 2D trophic predictor can be constructed under a conservative **known coordinate uncertainty ≤12,500m** criterion, and under a permissive all-indexed-coordinate sensitivity.

For every bat species × fixed requested 29 countries:
1. Bat sample records from original full archive occupy ≥5 distinct 25-km country-cells (strict known-precision primary). The same bat occupies ≥20 25-km country-cells **outside** the heldout country. These are recorded cells, not independent station occupancy.
2. Exclude **every NeoBat source publication RefCode** with any site in the heldout country from the training network, and exclude all interactions from the heldout country itself.
3. Retain source links with \`Interaction=Frugivory\`, \`TrophicGuild=Frugivore\`, source-name exact accepted plant cohort and source-name primary bat candidate cohort. Retain only plant names with ≥5 known-precision indexed plant cells in that heldout country, and ≥2 independent training \`RefCode\` covering the remaining links.
4. Define \`INPUT_POSSIBLE\` when ≥3 different retained plant partners and ≥2 training source reference codes survive. Otherwise \`INPUT_INDETERMINATE\`, not an ecological absence, trophic disconnection, or negative model effect.
5. Run the same **descriptive** gate using all indexed-coordinate cells (without an uncertainty condition); do not use this permissive result as a high-precision confirmation.
6. Keep all 26 bats and all 255 strict-match plants in the denominator. Never select the strongest species via eventual heldout model performance.
7. Output only species/country aggregate cell counts, partner count and bibliography count, plus the four plant names with no usable GBIF source rows. Do not commit exact coordinates, GBIF IDs, occurrence/event IDs or all original raw rows.

**Scientific claim ceiling:** availability of data to fit a *potential* trophic feature within a heldout-country design, not plant occurrence probability, actual fruit biomass, co-location within the same cell, occupancy/detection-corrected presence, or predictive M3−M1 superiority. This diagnostic is not eligible to be called an independent post-discovery test.

The input source is the already verified GBIF bat DOI 10.15468/dl.nxu727, plant DOI 10.15468/dl.xwc5zf, each with SHA256 receipts and 50-column GBIF TSV headers, plus original NeoBat study-location/reference tables fixed by author commit d25292d19be32a85a21c60384a3f2d818e8081de.
