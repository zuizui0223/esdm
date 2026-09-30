# E5 candidate screen: SNAPSHOT USA 2024

Status: **E5_CANDIDATE_NOT_QUALIFIED**

This is a response-blind candidate screen under the frozen E5 activity–detection
qualification contract. No biological sequence rows, focal taxon counts, diel outcomes,
or predictive scores were opened.

## Why the candidate is attractive

SNAPSHOT USA 2024 is independent of the E2–E4 MICA response and Snapshot Japan 2023.
The public metadata describe 3,127 deployment rows, 3,124 reported unique deployment IDs, 2,715 physical camera locations,
184 arrays across 49 U.S. states and 12 ecoregions.

The especially useful feature for E5 is an explicit camera-distance calibration programme.
Seventy-three arrays (918 camera locations) contributed calibration-distance observations
using reference signs placed every 3 m to 24 m or the maximum detection distance. This is
the kind of auxiliary detection-information path that E4 lacked.

## Why it nevertheless fails the frozen E5 gate

The E5 contract requires at least six distinct calendar months of exposure in both the
training and heldout domains. The complete published 2024 dataset spans only
2024-08-01 through 2024-12-19: **five calendar months**.

Therefore G6_TEMPORAL_SUPPORT fails before any focal response is opened.

No threshold is lowered, no sequence file is inspected, and no model fit is authorized.

## Gate summary

- G1 independent source: PASS
- G2 schema/effort/time fields: PARTIAL — fields declared, row values/identity uniqueness unverified
- G3 geography × source crossing: PENDING deployment-level metadata cross-tab
- G4 detection identification: PROMISING, but calibration-to-deployment linkage still required
- G5 physical replication: capacity PASS; split not yet frozen
- G6 temporal support: **FAIL (5 months < frozen minimum 6)**
- G7 model freeze: NOT REACHED

The candidate is terminal for the single-year 2024 E5 route. A broader independent
multi-season candidate may be screened separately without changing this result.
