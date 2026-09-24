# v0.6c Infrastructure Repair

Initial authorized run: `36014064564`
Initial authorized head: `f6b06c5bd8297703bed4f4d6207856a08e17988d`

The deterministic qualification completed successfully and is a valid frozen
qualification outcome.

Replicate 8 then stopped before returning any scientific record with:

`DesignUninformedError: process sp:accessibility has no process->channel->targeted-stream path`.

Cause:

- training models correctly declared accessibility information through their auxiliary
  stream;
- the held-out scoring model retained only `base_joint`;
- `base_joint` consumes both `log_intensity` and `log_accessibility`, but its
  `informs` metadata listed only `suitability`;
- `Model.check_design()` therefore rejected the held-out scoring model before posterior
  scoring.

This is a design-metadata wiring error, not a likelihood, truth, budget, seed, threshold,
or MCMC change.

Repair:

- only the held-out scoring copy of `base_joint` declares
  `informs={"suitability","accessibility"}`;
- its observation equation, effort, detection, targets, held-out data, ecological
  processes, and posterior samples are unchanged;
- training Direct and MatchedJoint models are unchanged;
- the frozen v0.6c gate and gate blob are unchanged.

The original one-shot authorization marker is removed in the repair commit.

A replacement run may be authorized only after the repaired contract tests pass. It must
reuse the exact frozen gate, seed family, MCMC profile, and thresholds.
