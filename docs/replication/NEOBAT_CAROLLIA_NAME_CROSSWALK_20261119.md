# NeoBat phase-1 taxonomic crosswalk amendment — 2026-11-19

Stage: prefit, read-only GBIF species-name audit. No bat occurrence coordinates,
plant models, held-out predictions or ecological outcomes were opened.

## The observed mismatch

25 of 26 NeoBat primary candidate bat-name strings matched the GBIF species
service exactly. *Carollia brevicauda* instead returned matchType=FUZZY,
rank=SPECIES, status=ACCEPTED, confidence=97, usageKey=2433177, recognized
name *Carollia brevicaudum* (Schinz, 1821).

## Independent species-concept evidence

- Mammal Diversity Database: https://www.mammaldiversity.org/taxon/1004873/
  accepts *Carollia brevicauda*, calls the alternate -um spelling a printer error.
- GBIF Catalogue of Life: https://www.gbif.org/taxon/5XDMH
  accepts *Carollia brevicaudum* and lists *C. brevicauda* as a synonym.
- ITIS: https://www.itis.gov/servlet/SingleRpt/SingleRpt?print_version=PRT&search_topic=TSN&search_value=1148804
  documents the correspondence.

## Correction and boundary

Accept only the explicit one-to-one name crosswalk:
Carollia brevicauda -> GBIF taxon 2433177, if the API returns
species rank, status ACCEPTED, matched scientificName beginning
Carollia brevicaudum, FUZZY confidence >=90.

Keep the original NeoBat name in the manifest. Label the admitted record
GBIF_COUNTS_AUDITED_ALIAS rather than treating it as EXACT. Do not relax
other fuzzy-match cases.

This is a taxonomy interoperability correction made before spatial-response
model evaluation, not a revision of an ecological hypothesis. It does NOT
establish usable independent 25-km occurrence cells, a citable GBIF download
DOI, or support for trophic prediction.
