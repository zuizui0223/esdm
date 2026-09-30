# E4 MICA exact-sparse empirical result

Status: **terminal exploratory empirical result**

E4 is a separately named computational-equivalence programme following the terminal E3
dense-grid infrastructure timeout. It does not reopen E3 and does not change the frozen
v0.4-R5b scientific model.

## Why E4 exists

E3 represented each deployment on the global deployment × DOY × hour Cartesian product.
The NumPyro likelihood later masked structurally unexposed cells, but latent fields and
rate arrays were still materialized for those cells first. The frozen E4 transformation
removes a context before latent-field construction iff every retained observation stream
has structural exposure false there.

This transformation is exact: a removed cell has zero likelihood contribution for every
parameter value, and nonzero data outside the retained union fail closed.

Frozen geometry:

| partition | dense contexts | retained contexts | reduction |
| --- | ---: | ---: | ---: |
| training | 615,020 | 11,531 | 53.34× |
| east heldout | 560,012 | 10,168 | 55.08× |

No prior, covariate, ecological process, observation likelihood, response mapping,
training/heldout split, MCMC setting, seed, or score definition changed.

## One-shot empirical result

Workflow run: `36622802225`  
Result artifact: `11059622869`  
Result JSON SHA256:
`34124094e6c25db04465cc1ff869af5813326729e6fd3b658a0921c45bc6f3e2`

All three fits completed with zero divergences. All 733 heldout deployments have unique
row-level absolute scores, and the row means reproduce the aggregate scores exactly.

| comparison | heldout score | gain vs knockout |
| --- | ---: | ---: |
| Full | -7.6929864071241045 | — |
| Activity knockout | -7.053935226712387 | activity gain = **-0.6390511804117178** |
| State knockout | -7.701377332147147 | state gain = **+0.008390925023042506** |

Frozen decisions:

- activity predictive support, descriptive: **false**;
- state predictive support, descriptive: **true**;
- confirmatory replication: **false**;
- causal claim: **false**;
- parameter-recovery claim: **false**;
- E3 rescue: **false**;
- same-programme rerun: **not allowed**;
- post-result retuning: **not allowed**;
- Laplace/INLA switch within E4: **not allowed**.

## Post-result transfer-tail audit

The negative activity result is strongly heterogeneous rather than uniformly negative.

- across all 733 deployments, many zero-event sites have tiny positive gains, but among
  the **128 event-bearing deployments, 127 have negative activity gain**;
- the worst 10 deployments account for about **43.2%** of total negative activity-loss
  magnitude and the worst 50 about **90.8%**;
- activity gain correlates strongly negatively with labelled focal-event count
  (`r ≈ -0.884`);
- the strict east holdout lies entirely outside training eastness support:
  training z about **-0.94 to 1.65**, heldout about **3.20 to 8.49**;
- a D-prefixed heldout source stratum absent from the training annotated stratum contains
  about **99.0% of focal events** and **99.6% of negative activity-loss magnitude**;
- the raw night/day event-rate ratio shifts from about **13.4** in training annotated
  exposure to about **3.0** in heldout exposure;
- posterior-mean activity at observed heldout focal-event contexts is about **0.185**,
  compared with the activity-knockout baseline **0.438**.

The bounded working hypothesis is therefore **transfer tail risk under combined
process-specific covariate and source-domain shift**: a stationary activity relationship
learned in the training annotated stratum suppresses expected counts when transferred
far outside its training support and into a heldout source domain with a markedly weaker
diel contrast.

This is a post-result exploratory diagnosis. It does not identify a causal geographic,
country, source-network, camera-protocol, or behavioral mechanism; it does not prove
activity is biologically irrelevant; and it cannot change the frozen E4 result.

The small positive state gain is also heterogeneous: among event-bearing deployments,
**58 gains are positive and 70 negative**, with positive gain concentrated in deployments
containing group events. It should not be described as a broad or confirmatory state
effect.

## Canonical records

- `docs/replication/E4_MICA_SPARSE_FROZEN_RESULT.json`
- `docs/replication/E4_MICA_POSTRESULT_TRANSFER_TAIL_AUDIT.json`
- `docs/replication/E4_MICA_POSTRESULT_TRANSFER_TAIL_RECEIPT.json`
- `docs/replication/E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json`
- `docs/replication/E4_MICA_POSTRESULT_SOURCE_DOMAIN_SUPPLEMENT.json`
- `docs/replication/E4_MICA_POSTRESULT_LOCATION_ROBUSTNESS_SUPPLEMENT.json`
- `docs/replication/E4_MICA_POSTRESULT_DIEL_NONSTATIONARITY_SUPPLEMENT.json`
- `docs/replication/E4_MICA_SPARSE_FIT_CONTRACT.json`
- `docs/replication/E4_MICA_SPARSE_NUTS_CONTRACT.json`
