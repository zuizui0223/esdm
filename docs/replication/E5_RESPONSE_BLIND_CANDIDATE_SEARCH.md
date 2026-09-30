# E5 response-blind candidate search

No focal response has been opened for E5.

The first candidate screen was deliberately based only on public study design, schema,
effort/time coverage, geography, physical replication, and detection-calibration
information.

## Immediate result

Two superficially attractive candidates fail the frozen E5 gates **before response
opening**.

### SNAPSHOT USA 2024

This is a large, independent and unusually well documented dataset: 3,127 deployment
records, 2,715 named sites, 184 arrays, 49 states and 12 ecoregions. Seventy-three arrays
also participated in camera-distance calibration.

It nevertheless fails the frozen E5 temporal-support gate. The published 2024 data span
August through December, only five distinct calendar months, while E5 requires at least
six distinct calendar months in both training and heldout exposure. It is therefore not
eligible for an E5 outcome opening.

### Nakashima et al. double-observer surveys

This design is excellent for detection identification: paired cameras observe the same
small focal area from different directions and the paper directly estimates missed
detections. It also contains two very different geographic regimes, Japan and Cameroon.

It still fails the frozen E5 geometry. The field surveys use 7 stations in Japan and 26
in Cameroon, so no strict cross-geographic split can satisfy >=20 training and >=10
heldout independent physical locations. The Japan and Cameroon survey windows each span
only four calendar months, also failing G6.

## Current discovery strategy

The strongest search universe is now **Wildlife Insights public projects**, not a
particular focal-response dataset. Public downloads separate projects/cameras/deployments
from detections, and project metadata include sensor layout, paired/clustered cameras,
sensor method and stratification. This permits a genuinely response-blind search.

The next screen should use metadata only and require all of the following simultaneously:

- at least six calendar months of exposure in both candidate regimes;
- >=20 training and >=10 heldout independent physical locations;
- paired/clustered sensors or another identifiable detection-calibration path;
- geography crossed with project/source/protocol rather than perfectly confounded;
- enough metadata to freeze source/region × diel and season × diel terms before outcome.

Species-specific counts, diel directions, state frequencies and predictive scores remain
forbidden during candidate selection.
