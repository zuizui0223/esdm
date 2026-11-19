# NeoBat original bat DOI target-group pseudo-background: empirical input quantity gate

Date: 2026-11-19. Frozen design: `NEOBAT_BAT_TARGETGROUP_BACKGROUND_SOURCE_GATE_FROZEN_20261119.md`. Source-free regression: [Actions #44531810088](https://github.com/zuizui0223/esdm/actions/runs/44531810088) PASS. Original DOI one-shot: [Actions #44531915649](https://github.com/zuizui0223/esdm/actions/runs/44531915649) PASS.

Exact original 85,912-record bat ZIP SHA `fc94ff92a127ec22655733a0b0cdaf12b5b24794fcc0129532e8a1e49fe856f0`; source-verified country×species strict cell counts exactly replayed. No bat coordinate, cell ID or GBIF record committed. Final aggregate receipt: `docs/replication/neobat/bat_targetgroup_background_gate.json`.

## Primary source-feasibility result (original 84 denominator)

- **80/84** country-heldout bat taxa have >=5 strict 25-km focal presence cells plus >=5 distinct-cell target-group background cells in the withheld country, and >=20 each outside it for training.
- **4/84 source STOPs** (not inferred animal absences):
  - *Artibeus jamaicensis* × Dominican Republic (DO): 15 focal strict cells / 0 other-bat background cells.
  - *Artibeus jamaicensis* × Jamaica (JM): 5 / 0.
  - *Artibeus jamaicensis* × Puerto Rico (PR): 10 / 0.
  - *Artibeus lituratus* × Argentina (AR): 5 / 4.
- On all 80 source-qualified pairs, >=5 of the withheld-country target-background cells are represented by at least one GBIF `datasetKey` also observed for the focal bat *within that country*. The analogous source-key condition is >=20 in training. **The shared dataset key is not matched event sampling, detection completeness or absence evidence.**
- Intersection with prior independently checked 106-plant source input qualifications is **79/84**. One additional v2 failure, *Sturnira tildae* × Colombia (CO), retains only 2 documented partner plant names after fixing the 106-plant universe.

## Scientific ceiling

This only establishes that a plant-independent **relative bat occurrence rank vs other-bat recorded target-group cells** is possible for many prospective folds. It is not true occupancy, species-specific absence, causal feeding, independent test data, 3D habitat, or proof of M3 superiority. Other species records are suitable as **pseudo-background only**, and all data were previously source-inspected. Do not treat the 80 or 79 pairs as independent studies or silently drop stopped pairs from the 84-fold accounting.

## Next

Train **country-crossfitted 106-plant suitability** using published original plant DOI, exact immutable WorldClim climate/elevation sources, all original 255 plant species as the regional observation-effort target group if justified, and no plant occurrences from withheld country in any plant training. First test a frozen small taxon×country pilot with full nonleakage checks. Forest 17-country coverage and biogeographic sampling-effort controls still pending for full bat M0/M1/M3/N1 inference.
