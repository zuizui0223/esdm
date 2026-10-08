# Wild-pig activity-anchor empirical outcome: terminal QC interpretation

Recorded 2026-10-08. Primary route frozen before values; QC after outcome and explicitly exploratory.

## Two independent conclusions

**Frozen statistical outcome:** UNRESOLVED.

The one-shot run 37643401531 completed successfully. Its predeclared
8-transfer median gain was +0.007875718209424398. The 1,000-bootstrap 95%
interval for that gain was [-0.05019368081794174, +0.03124649854524571].
Six of eight point gains were positive. The confidence interval includes zero;
the frozen route does **not** support a transferable observation correction.

**Quality outcome:** HOLD_SAMPLE_IDENTITY.

The separate exploratory identifier-only run 37706547653 completed successfully,
verified the exact four pinned CA camera CSV blobs and found:

| Season | CSV rows | Missing LocationName rows | Raw unique labels | Normalized unique labels |
|---|---:|---:|---:|---:|
| Spring | 868 | 0 | 48 | 48 |
| Summer | 1,475 | 0 | **434** | **434** |
| Fall | 2,053 | 0 | 48 | 48 |
| Winter | 917 | **194** | 47 | 47 |

All 48 of the spring/fall labels occur in summer. The remaining 386 labels
occur in summer only; 383 summer labels are singletons. Trim, Unicode NFKC,
casefold and whitespace normalization do not reduce 434.

The study's public methods report 48 California physical cameras. Its public
source code counts `length(unique(tmp$LocationName))` without a documented
physical-site crosswalk. Therefore **434 distinct LocationName strings are not
434 known independent physical cameras.** The content of those 386 extra strings
has not been inspected or released in this audit, and their actual origin
cannot be asserted.

### Different implications for point estimates and uncertainty

The frozen runner computes a camera point activity curve from all *retained*
camera-event times, then groups times by `LocationName` to bootstrap camera
sites. Conditional on the same retained event rows, changing only the ID
assignment leaves the pooled point curve unchanged but changes bootstrap
resampling units, weights and confidence intervals.

- CA summer: the runner treated 434 labels as independent camera-site clusters
  even though the published physical deployment design had 48 cameras; the
  site-cluster bootstrap therefore lacks a demonstrated physical-unit basis.
- CA winter: 194 of 917 released rows have missing LocationName, consistent
  with the original runner using 723 retained camera events. Missing-ID
  selection could also affect point activity shape; whether those 194 rows
  differ in diel distribution was not tested and cannot be assumed either way.
- The main 8-transfer result combines the original unaltered camera curves
  and their original 1,000 site-label bootstrap replicates. It must not be
  retroactively corrected or treated as physically validated.

The frozen UNRESOLVED label and separate QC hold coexist: the former is the
mechanical result under the implemented labels, the latter limits scientific
inference from its estimated uncertainty.

## Ecology and originality boundary

The alternate external-GPS-anchor question concerns whether relative
camera observation distortion can transfer across Florida and California.
This remains **not established**. Neither a non-zero detection bias, its cause,
nor a geographic difference in sensor behavior has been isolated.
Source camera configurations also differed between regions (Florida 10-image
bursts plus a 5-minute quiet period; California 3-image bursts without a quiet
period), so geography and sensor protocol cannot be causally separated by
this two-region comparison alone.

The result is neither a validation of the original direct-detection E5 G4
(which remains unpassed) nor a demonstration that all camera/telemetry
comparisons lack biological meaning.

## Integrity and next legitimate evidence

Original one-shot workflow: https://github.com/zuizui0223/esdm/actions/runs/37643401531

Post-outcome identifier-QC workflow:
https://github.com/zuizui0223/esdm/actions/runs/37706547653

Original paper: https://doi.org/10.1002/ecs2.4728

Pinned public source:
https://github.com/dwwolfson/gps_cameratrap_activity_comparison/tree/bc97ff80ec91aba03f58f06629c7e8dfff9eb85d

The ideal external repair would be an independently documented mapping of all
published `LocationName` labels to the original 48 physical cameras, together
with camera deployment/effort and missing-ID documentation. Such a crosswalk
does not appear in the frozen outputs and must not be guessed.

One may perform a separately authorized, explicitly exploratory lexical
diagnostic of identifiers, but it must not rewrite the original run, invent
physical identities, select favorable seasons/directions, or be called
preregistered validation.
