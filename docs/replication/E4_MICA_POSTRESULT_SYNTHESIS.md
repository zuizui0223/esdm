# E4 MICA post-result synthesis

E4 is closed. This note summarizes the already-frozen result and its post-result
diagnostics; it does not authorize another E4 fit, retuning, or backend switch.

## What is robust

The one-shot exact-sparse empirical fit completed with zero divergences on 733 east-heldout
deployments. The frozen gains are:

- activity: **-0.639051**
- state: **+0.008391**

The activity result remains negative under both ODSP uncertainty schemes:

- 733 deployment blocks: **95% interval -0.8381 to -0.4400**
- 27 physical-location blocks: **95% interval -1.2594 to -0.01870**

Thus the activity channel, as frozen and transferred, is **robustly non-generalizing in
this endpoint**. The small positive state gain is not robust: its intervals cross zero
under both block definitions.

## What the failure looks like

The activity failure is highly heterogeneous.

- 127 of 128 event-bearing heldout deployments favor the activity knockout.
- The worst 50 deployments carry about 90.8% of negative activity-loss magnitude.
- Collapsing 733 deployments to 27 physical locations leaves 19 of 20 event-bearing
  locations with negative activity gain.
- Every leave-one-location-out deployment-weighted activity mean remains negative.
- The D-prefixed source stratum contains about 99.0% of heldout focal events and about
  99.6% of the net activity-loss magnitude.

The magnitude is therefore source-domain concentrated, although the negative direction
is not unique to that source domain.

## Why this is not simply a muskrat story

The training annotated stratum has a much stronger night/day event-rate contrast
(~13.4) than the heldout D source domain (~2.96), and this contrast change persists
within seasons.

A cross-taxon negative control reaches the same qualitative pattern in most eligible
species: 7 of 8 eligible binomial taxa have a lower heldout-D night/day ratio, including
6 of 7 nonfocal taxa. Muskrat ranks only sixth in negative shift magnitude.

That makes a muskrat-specific behavioral explanation insufficient on its own.

## What remains unidentified

The annotated observation stream fixes detection at 1.0. At the same time, geography,
source domain, deployment metadata, annotation metadata, and diel structure all shift
between training and heldout data.

E4 therefore cannot identify whether the transferred activity failure arises from:

1. ecological activity nonstationarity,
2. effective camera/event-detection nonstationarity,
3. annotation/event-yield differences,
4. or a mixture of these.

The correct empirical statement is about **predictive transfer failure of the frozen
activity channel**, not a causal statement about muskrat behavior.

## What a genuinely new test must do

A future E5 programme should not reopen E4. Before any new response is examined it should
require independent data that cross geography with survey/source domain, explicitly
measure or model effective detection, use physical locations as clustering units, and
freeze region/source × diel and season × diel terms in advance. Shared-network nonfocal
taxa should be retained as predeclared negative controls.

Canonical machine-readable synthesis:
`docs/replication/E4_MICA_POSTRESULT_SYNTHESIS.json`.
