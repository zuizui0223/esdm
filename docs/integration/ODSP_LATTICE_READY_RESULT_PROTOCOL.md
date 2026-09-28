# ODSP lattice-ready result protocol v1

This protocol is for future eSDM programmes in which two or three ecological
information blocks are scientifically unordered and downstream ODSP should be
able to audit every admissible information-addition order.

It is a serialization protocol, not a new inferential method.

## Why it exists

A pair of one-step transfer contrasts is not enough to reconstruct a complete
information lattice.

For two blocks A and B, ODSP requires four absolute held-out score nodes:

- base
- base + A
- base + B
- base + A + B

For three blocks, all eight subset nodes are required.

Missing nodes may not be reconstructed from stored gains.

## Prospective rule

A future eSDM result intended for lattice audit must freeze before outcome
scoring:

- fixed base information;
- two or three named, variable-disjoint information blocks;
- the complete Boolean subset model/knockout set;
- one absolute held-out score field for every subset;
- common held-out rows;
- common proper score and reference measure;
- group identity;
- validation-block identity when paired certification is intended.

The result artifact must store those absolute scores directly.

## Current scope

Version 1 supports exactly two or three unordered information blocks.

This matches the currently qualified ODSP complete-lattice family sizes:

- 2 blocks -> 4 nodes -> 4 directed edges
- 3 blocks -> 8 nodes -> 12 directed edges

Four or more blocks are not authorized by this protocol.

## R5b boundary

The frozen R5b activity and state results do not become a lattice retroactively.

R5b stores:

- activity knockout;
- state knockout;
- full activity + state.

It does not store the common suitability-only node. Therefore the complete
two-block score table is absent.

The protocol fails closed rather than synthesizing that missing baseline.

## Example

A future three-block process programme might predeclare:

environment as fixed base, with added blocks:

- movement;
- activity;
- interaction.

It must then save absolute held-out scores for all eight subsets before ODSP can
audit order sensitivity.

The eSDM serializer can write those scores and a manifest, but it does not itself
run ODSP inference.

## Boundaries

This protocol does not:

- add a new scientific result;
- alter the current transfer-source registry;
- authorize a global information ladder;
- combine sources from different frozen programmes into one lattice;
- select the best order after outcome access;
- authorize EOG consumption;
- rank survey locations;
- authorize N4 action.

It only ensures that future result artifacts retain enough information for an
existing ODSP lattice audit to be possible without reconstruction.
