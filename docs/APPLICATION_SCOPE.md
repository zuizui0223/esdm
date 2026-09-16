# Application scope: ecological interactions beyond any single domain

`esdm` is designed as a generic process-based community model. No biological domain is the privileged use case.

Pollination is retained only as one example because it is easy to explain in terms of state overlap, realized encounters, and functional consequences. It must not define the runtime API, benchmark universe, or manuscript claim ceiling.

## Broad application families

| Interaction family | Example latent process | Candidate observation streams | Typical claim ceiling without intervention |
| --- | --- | --- | --- |
| Competition | partner latent density modifies focal growth/state use | repeated abundance, occupancy, resource use, telemetry | predictive / realized association; causal only with stronger design |
| Predator–prey / consumer–resource | predator activity overlaps prey latent intensity and state | camera traps, kill/feeding events, telemetry, diet/eDNA | realized encounter/consumption when directly observed |
| Host–parasite / pathogen | host latent availability and vector/parasite state alter infection hazard | infection assays, host surveys, vector traps, longitudinal sampling | realized infection association; transmission mechanism may remain unresolved |
| Herbivory | consumer latent activity overlaps host tissue/state | damage surveys, feeding events, exclosures | realized/functional with damage or fitness endpoints |
| Facilitation | facilitator latent field modifies establishment or persistence | demographic plots, microclimate sensors, transplant/survival data | functional when demographic benefit is measured |
| Ecosystem engineering | engineer state changes habitat field used by other taxa | habitat structure, occupancy, remote sensing, repeated surveys | habitat-mediated association unless manipulated |
| Mutualism | partner latent state modifies focal performance | encounter/service events plus demographic response | functional if benefit is measured for focal; reciprocal mutualism needs both sides |
| Seed dispersal | frugivore/transport latent field couples to plant propagule movement | fruit removal, GPS, seed traps, genetic assignment | realized transport / functional recruitment depending endpoint |
| Pollination | visitor latent activity overlaps flowering state | visitation, pollen transfer, seed set | one example of realized/service/functional tiers |
| Commensal / nesting association | one taxon's structures or occupancy create opportunity for another | nest/den surveys, repeated occupancy, video | association/facilitation only as evidence permits |

## Design rule

Domain labels never determine mechanism. The same generic objects should represent all cases:

```text
focal latent field
+ partner latent field
+ state compatibility / process kernel
+ observation stream
-> posterior interaction contribution
-> evidence-tiered claim
```

Observed partner records are not inserted directly as ecological covariates when a partner latent field is the intended biological quantity.

## Benchmark universe

Future known-truth benchmarks should cover at least:

1. no interaction, shared measured environment;
2. no interaction, hidden common driver;
3. resource/state partitioning;
4. antagonistic directed effect;
5. beneficial directed effect;
6. consumer–resource tracking with time lag;
7. host–parasite dependence with imperfect detection;
8. habitat engineering mediated through an environmental state;
9. network rewiring without change in taxon composition;
10. reciprocal interaction as an intentionally unsupported/cyclic v0 case.

The goal is not to predict one interaction type. The goal is to determine which ecological process layers are informed, identifiable, transferable, and claimable from a given combination of observation streams.
