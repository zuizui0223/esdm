# v0.5a Directed Partner Identification Qualification Results

Status: **FAIL**

v0.5a tested whether the first directed partner-latent coefficient could be qualified
before any replicated MCMC outcome.

The target was `focal.partner_effect.beta_partner`.

## Frozen provenance

- qualification run: `35961662115`
- qualification head: `a90984450ba9e29644e0acf7f42ab5180a54762d`
- gate freeze commit: `d5f8d3e10c059cedfb8c3efbf5a1d232efa3507d`
- gate blob expected/observed:
  `c5d43c4baa01d631704e6769db8eed49ec85837b`
- artifact ID: `10792168843`
- artifact / independently verified ZIP SHA256:
  `a2d5ff9e78694ecc5f300333649996cec01b17026ed14541b121aa0c3b3db9f7`

The artifact reports `infrastructure_block = null`.

## Mechanical result

Three of four frozen qualification terms passed.

### directed_positive: beta = +0.80

- structural identification: **PASS**
- practical target SD proxy: **0.21144**
- frozen threshold: <= 0.25
- practical identification: **PASS**

### interaction_null: beta = 0

- structural identification: **PASS**
- practical target SD proxy: **0.48465**
- frozen threshold: <= 0.25
- practical identification: **FAIL**

Therefore v0.5a qualification is **FAIL** and no replicated MCMC outcome is authorized.

## Interpretation

The partner coefficient is not structurally confounded in either world. The failure is
practical precision specifically near the null.

A strong positive partner effect raises the focal observation rate and is estimable under
this design. At beta = 0 the same abundance-only design contains too little information
to support a precise absence claim.

The supported methodological conclusion is:

> An observational design can estimate a sufficiently strong biotic effect while still
> being unable to demonstrate precisely that the effect is absent.

That asymmetry makes a positive-only recovery benchmark insufficient for v0.5.

## Next design consequence

The next fresh hypothesis should not lower the target-SD threshold or retune beta. It
should add source variation that is informative about focal response independently of the
focal environmental surface.

A prospectively assigned source-only perturbation / source-gradient design is therefore
the next v0.5 candidate.

## Claim boundary

Because the null practical gate failed:

- no MCMC recovery/transfer run is permitted under v0.5a;
- no `PREDICTIVE_DEPENDENCE` promotion is made;
- no REALIZED, FUNCTIONAL, or CAUSAL interaction claim is made.

The v0.5 partner-latent runtime core remains valid and fully tested. This FAIL applies to
the first validation design, not the process implementation.
