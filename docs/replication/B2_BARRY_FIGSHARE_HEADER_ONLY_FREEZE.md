# B2 Barry: pre-response frozen original Figshare CSV header audit

**2026-11-19, before opening biological-response rows of any Barry CSV.** B1 source-manifest run [44473610678](https://github.com/zuizui0223/esdm/actions/runs/44473610678) verified official article ID 16821361 and original file names, IDs, sizes, and published MD5s, with zero original data-file downloads and zero animal rows opened.

## Pinned original CSV inputs and limits

- `CamStations_Ecosphere.csv`, ID **31117351**, **211555** bytes, MD5 **0c9963ee9a52fdf6d05c15ed1d13193c**.
- `DogTracks_Ecosphere.csv`, ID **31117348**, **951580** bytes, MD5 **f3ae1ac01ad3b0b48d909a3f86845552**.
- `WestOR_grid_Ecosphere.csv`, ID **31117429**, **1105856** bytes, MD5 **ca5b3a850474ce09cf2a75d8c667e898**.

Original archive [Figshare article 16821361, v1](https://doi.org/10.6084/m9.figshare.16821361.v1). Fixed public download endpoints `https://ndownloader.figshare.com/files/{ID}`. Each file must exactly pass source bytes + MD5 before reading its header. No alternative file/record selector is authorized. Hashing all original bytes is allowed for provenance but only the first newline-terminated CSV header may be **parsed**. No biological data row, camera station coordinate value, dog-track detection/scat record, sensitive species coordinate, or image is extracted or exposed.

The output records only full ordered column names, number of header columns, source SHA256, and matches to five predeclared column-name concept families: station/unit, ecoregion, method/detector, effort/time and observation/presence. A keyword hit is not evidence that the column is populated or that G3 crossed geographic-source sampling or G4 independent detection identification passes. Stop on source byte drift or malformed header, and preserve exact terminal status and hashes. Only one PR-opening workflow is allowed; retire before merging.

**Next (not authorized by B2):** a genuinely separate data design must demonstrate that `CamStations` and `DogTracks` share stable **3×3 km sampling-unit** identifiers; that camera and detector-dog sampling cross ecoregions and months at the required granularities; and that the observation structure can identify actual detection under original E5 G4 conditions rather than treating dog scat as a complete reference of camera-zone missed passages. Freeze any biological response design *before* parsing the data rows. The prior E5 registry remains 0/17 qualified, and Safari14/C1–C3/D1/E4/E5/E7 conclusions remain untouched.
