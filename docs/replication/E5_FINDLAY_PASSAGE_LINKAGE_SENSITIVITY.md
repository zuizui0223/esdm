# E5 Findlay passage-cohort sensitivity (retrospective, aggregate only)

The immutable Findlay CCTV receipt has FOX near (88 CCTV passes, 55 triggers,
19 registered) and far (175 passes, 47 triggers, 27 registered).
Equality of triggered counts in separate source files is not proof of
passage-level linkage.

Define a *hypothetical* upper bound k on mismatched capture outcomes
in **each** of these two equally sized registration cohorts.
With no changed CCTV denominators, near registered counts could lie
in [19-k,19+k] and far in [27-k,27+k], clipped to [0,55] and [0,47].
This is an exploratory deterministic sensitivity test, not an estimate
of observed mismatches or a sampling confidence interval.

- The apparent higher near-than-far final recorded fraction can disappear
  with k=4: (19-4)/88 <= (27+4)/175.
- The higher conditional registration at far distance can disappear
  with k=6: (27-6)/47 <= (19+6)/55.
- Neither direction is therefore identity-validated; there is no
  demonstrated finite k bound without a per-passage crosswalk.

For BADGER far, 16 triggered CCTV passes but only 15 registration-eligible
records were found. **Only under the unverified condition** that 15 rows
are genuine members of the 16 passages and exactly one outcome is missing,
recorded-per-pass is bounded by [8/82,9/82]. This is a conditional
scenario, not a repaired or identified original estimate.

The opposite trigger/registration stage shifts in FOX could arise
partly from composition selection among passages that successfully
triggered (e.g. passage speed or trajectory); such an ecological mechanism
is a hypothesis, not inferred here.

No source CSV was opened, no frozen run was repeated, and the original
Findlay count-aligned descriptive result is unchanged. E5 original
qualification is still 0/17; G4 unpassed. Wolfson UNRESOLVED/QC HOLD
and Rhode Island original G4 hard stop remain unchanged.
