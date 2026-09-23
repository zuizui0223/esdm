# v0.4-R4 Balanced Temporal Allocation Design

Status: **approved prospective design, pre-qualification**

Base: frozen R3a FAIL branch head
`50d1d1dcf0fca775ada21ccf959d6a081fdb316d`.

R4 starts a new prospective observation-design hypothesis after the frozen R3a negative
result. R3a remains a valid FAIL and is not retuned.

## Scientific question

R3a held the state-annotation budget at 432 contexts and redistributed it from
18 sites × 24 temporal contexts to 36 sites × 12 temporal contexts. Structural
identification remained intact, but practical precision still failed under the frozen
R2 target-SD rule.

The R3a temporal selector was a joint four-dimensional cyclic maximin design. That design
optimizes geometric coverage, but it does not guarantee balanced marginal representation
of the seasonal and hourly contrasts that enter the activity and state channels.

R4 asks a different question:

> At the same 36-site × 12-time × 432-context budget, does an explicitly phase-balanced
> Cartesian temporal design improve practical separation of activity and state slopes
> relative to joint temporal maximin coverage?

## Isolated intervention

R4 changes only the positive StateAnnotatedCount temporal allocation.

Unchanged from R3a/R2:

- 36 annotated spatial sites, using the exact R3a spatial maximin sequence;
- 18 calibrated PresenceOnly sites × all 24 temporal contexts;
- broad opportunistic PresenceOnly stream;
- ecological, observation, activity, and state truth;
- annotated effort and detection;
- held-out east geometry;
- all 13 identification targets;
- all three R2 anchors;
- all structural/practical thresholds;
- sparse practical-refusal control;
- unknown annotated-detection refusal control;
- total positive annotated budget = 432 contexts.

## Frozen temporal design principle

The frozen temporal domain contains six DOY values and four hour values.

R4 selects three seasonal phases by taking every second ordered DOY beginning with the
first declared DOY, and crosses those phases with all four declared hour phases.

For the frozen domain this is exactly:

- DOY: 15, 135, 255;
- hour: 0, 6, 12, 18;
- Cartesian product: 3 × 4 = 12 temporal contexts.

Therefore each selected seasonal phase occurs four times and each hourly phase occurs
three times.

This selector uses only declared domain coordinates. It does not inspect counts,
parameter values, anchors, Jacobians, Fisher information, target-SD values, R2 results,
or R3a results.

## Why this is a new hypothesis rather than a retune

R3a tested geometric maximin coverage in joint cyclic time coordinates.

R4 tests marginal phase balance. The design principle is different and is frozen before
R4 qualification. No threshold is changed and no R3a weak-target value is used by the
selector.

The interpretation is therefore about observation geometry:

> coverage-optimal sampling and contrast-balanced sampling need not be equivalent for
> recovering distinct latent activity and state processes.

## Prospective sequence

1. implement and test the phase-balanced selector and fixture;
2. freeze an R4a qualification gate with the unchanged R2 thresholds and anchors;
3. verify the gate artifact is stable;
4. only then run R4a structural/practical qualification once;
5. record PASS or FAIL without changing the design.

R4a contains no MCMC. A full recovery/transfer gate may be created only after R4a PASS.

## Non-claims

R4 does not claim that balanced factorial designs are universally optimal, that R3a was
incorrect, that more spatial replication is always preferable, or that v0.4 is promoted.
