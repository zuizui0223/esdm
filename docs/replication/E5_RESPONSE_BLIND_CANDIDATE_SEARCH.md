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


## Two useful near-misses

### Uljin, South Korea 2022–2023

This public dataset is strong on duration and effort structure: 82 physical camera
stations were operated continuously from April 2022 to May 2023 with a camera-operation
log and station-level covariates. It therefore passes the frozen temporal and physical
replication minima on design metadata.

It still fails E5 G3. The network is one standardized study/source in one geographic
region (two local site strata), so geography cannot be crossed with an independent
survey/source domain. More data from the same network do not solve the E4 confounding.

### Eastern Amazon continuous jaguar monitoring, 2014–2020

This design has unusually long temporal coverage (March 2014–December 2020), 42 camera
locations, and paired cameras at 11 locations for parts of the study. Those features are
promising for G4–G6.

It is not qualified here. The published study is one geographic/source network rather
than a geography × source crossing, paired cameras did not always operate simultaneously,
and this screen did not establish a reproducibly accessible raw event/deployment package
meeting E5 G2. No response was opened to repair those deficiencies.

## Search status

Seven candidates/reference families have now been screened under the frozen criteria and
**zero are qualified**. This is not a scientific null result. It means the present
public candidates do not yet contain the design needed to separate transferred activity
from effective detection under the E5 contract.

The Wildlife Insights public-project universe remains the next response-blind search
space because project, camera and deployment metadata can be screened before detection
records are touched.
