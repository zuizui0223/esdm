# E5 candidate screen: Queensland Wet Tropics

Status: **E5_CANDIDATE_NOT_QUALIFIED**

Queensland remained the strongest named E5 candidate through multiple response-blind
checks. Its public design has matched road/bush cameras and a repeated-visit framework,
and the transformed VerbatimEvent material contains broad spatial and calendar coverage.

The decisive failure is at the required effort-metadata grain.

1. Direct Deployment check: **271/271** Deployment rows have empty `eventDate`, so
   zero deployment intervals can be constructed directly.
2. Survey-parent inheritance check: all 271 Deployments link uniquely to six parent
   Survey rows, but **6/6 Survey rows also have empty `eventDate`**. Therefore
   **0/271** Deployments can inherit a valid response-independent interval.
3. The diagnostic skipped 33,522 Trigger rows without decoding their dates. Inferring
   camera effort from first/last trigger or detection time remains forbidden because
   effort would then depend on the biological response.

Thus G2 fails and split-specific G6 cannot be constructed. G3/G4 are not promoted after
that hard stop.

No Event-core biological rows, eMoF values, Occurrence, VerbatimOccurrence, Multimedia,
species/taxon values, Trigger dates, or focal outcomes were opened. This is a metadata
qualification stop, not a biological negative result.
