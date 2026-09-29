# TR1 prospective trait-transfer gate v1

Status: **FROZEN BEFORE ANY TR1 OUTCOME EXECUTION**

TR1 asks whether measured taxon traits add held-out predictive information for
taxa that were entirely excluded from model fitting.

## Known-truth design

- 30 taxa total;
- 20 training taxa and 10 held-out taxa;
- trait values are fixed on an evenly spaced grid from -1.45 to +1.45;
- every third taxon beginning at index 1 is held out;
- every taxon receives the same 41-point environment grid from -2 to +2;
- no taxon random effect is generated.

Positive world:

logit P(Y=1) = -0.2 + 1.0 * environment + 1.0 * trait

Null world:

logit P(Y=1) = -0.2 + 1.0 * environment

Because the environment grid is identical for every taxon, trait cannot earn
predictive gain merely by proxying a taxon-specific environment distribution.

## Learners

Lower information:

environment-only logistic regression

Full:

environment + trait logistic regression

Both are unpenalized maximum-likelihood logistic fits with deterministic Newton
iterations. Taxon identity is never a predictor.

## Held-out score

The two models are scored on exactly the same rows from the 10 unseen taxa.

Score: mean held-out log predictive probability.

Required absolute fields:

- environment_only_heldout_log_score
- environment_trait_heldout_log_score

Trait gain is their difference.

## Replication

- positive world: 32 replicates;
- null world: 32 replicates;
- positive base seed 20261101;
- null base seed 20262101;
- stride 97.

## Oracle calibration

Before any stochastic outcome was opened, the frozen known-truth design implies
an expected held-out trait information gain of approximately

0.06306753955889005 nats per held-out context

in the positive world and exactly 0 in the null world.

The positive-world gate threshold of 0.03 therefore requires recovery of roughly
half of the known-truth oracle trait information rather than merely any positive
gain.

## Frozen positive-world gate


- mean trait gain >= 0.03;
- positive gain rate >= 0.75;
- absolute mean fitted trait-coefficient bias <= 0.15.

## Frozen null-world specificity gate

- material gain threshold = +0.01;
- at most 8/32 null replicates may exceed that threshold;
- null mean gain <= +0.005;
- absolute mean fitted trait coefficient <= 0.15.

The null gate protects the traits axis from generic extra-parameter optimism.

## ODSP readiness

Only the positive-world absolute scores are eligible for the downstream numeric
traits transfer axis:

environment_only < environment + traits

Each known-truth replicate is one independent population group.

The later ODSP population audit is descriptive and cannot change TR1 promotion.

## Fail-closed boundary

No threshold, seed family, taxon split, trait grid, environment grid, learner,
score, or held-out row definition may change after outcome access.

PASS supports transferable trait information only in this frozen known-truth
design. It does not establish empirical trait importance, phylogenetic effects,
causal trait effects, movement, interactions, or survey priority.
