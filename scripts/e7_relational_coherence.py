#!/usr/bin/env python3
"""E7 frozen-pair relational coherence: aggregate-only, post-outcome algebraic audit.

This reads no biological images, detections, locations or sequence rows and
never refits a latent ecological model. Pair-specific Mantel-Haenszel effects
were computed on differing camera subsets and are not independent.
"""
from __future__ import annotations

import argparse
import csv
from itertools import combinations
import hashlib
import io
import json
import math
from pathlib import Path
from statistics import median

SOURCE_JSON_SHA256 = "21a0b03d8c17442ddeeed79023ec28d23525c2815ca7a0bbaf54faec12e65f2a"
SOURCE_ARTIFACT_RUN = 39222089646
PAIR_CSV_SHA256 = "688bf6ff6d5289be6f577583f30a753f460bc53b03ca9c5d207a60f50d51951b"
COHORTS = ("discovery", "validation")
COLS = ("species_1", "species_2", "discovery_log_dry_over_wet",
        "validation_log_dry_over_wet", "discovery_status", "validation_status",
        "discovery_matched_sites", "validation_matched_sites")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for b in iter(lambda: handle.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rows_from_frozen_source(path: Path) -> list[dict]:
    """Regenerate the durable 66-pair table from the published-run aggregate."""
    if sha256_file(path) != SOURCE_JSON_SHA256:
        raise ValueError("original frozen E7 aggregate JSON SHA256 changed")
    j = json.loads(path.read_text(encoding="utf-8"))
    if j.get("status") != "E7_SERENGETI_INDEPENDENT_SEASONAL_ASSEMBLY_EXPLORATORY_RESULT":
        raise ValueError("source is not the frozen E7 terminal aggregate")
    roster = j["roster_selected_before_validation"]
    if len(roster) != 12 or len(set(roster)) != 12:
        raise ValueError("E7 twelve-taxon discovery roster drift")
    paired = {}
    for cohort in COHORTS:
        part = j[cohort]
        if part["possible_pairs"] != 66 or len(part["all_pairs"]) != 66:
            raise ValueError("all 66 original E7 pair rows required")
        pairs = {}
        for x in part["all_pairs"]:
            key = (x["species_1"], x["species_2"])
            if key in pairs:
                raise ValueError("duplicate original E7 taxon pair")
            pairs[key] = x
        paired[cohort] = pairs
    universe = list(combinations(sorted(roster), 2))
    if set(paired["discovery"]) != set(universe) or set(paired["validation"]) != set(universe):
        raise ValueError("pair roster differs from fixed 12 species")
    result = []
    for a, b in universe:
        x, y = paired["discovery"][(a,b)], paired["validation"][(a,b)]
        fields = [a, b]
        for z in (x,y):
            if z["status"] == "DESCRIPTIVE_ESTIMABLE":
                shift = float(z["relative_shift"])
                if not math.isfinite(shift) or shift <= 0:
                    raise ValueError("invalid original estimated shift")
                fields.append(repr(math.log(shift)))
            else:
                fields.append("")
        fields += [x["status"], y["status"], str(x["matched_distinct_sites"]),
                   str(y["matched_distinct_sites"])]
        result.append(dict(zip(COLS, fields, strict=True)))
    return result


def csv_bytes(rows: list[dict]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def load_pinned_pair_table(path: Path) -> list[dict]:
    if sha256_file(path) != PAIR_CSV_SHA256:
        raise ValueError("frozen E7 aggregate pair-table SHA256 changed")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLS:
            raise ValueError("E7 pair-table schema mismatch")
        rows = list(reader)
    if len(rows) != 66:
        raise ValueError("exact 66-pair frozen table required")
    taxa = sorted({v for r in rows for v in (r["species_1"], r["species_2"])})
    expected = list(combinations(taxa, 2))
    if len(taxa) != 12 or [(r["species_1"], r["species_2"]) for r in rows] != expected:
        raise ValueError("pair-table taxonomic roster/order changed")
    for r in rows:
        for cohort in COHORTS:
            label = r[f"{cohort}_status"]
            value = r[f"{cohort}_log_dry_over_wet"]
            if label == "DESCRIPTIVE_ESTIMABLE":
                if value == "" or not math.isfinite(float(value)):
                    raise ValueError("missing/nonfinite qualified log effect")
            elif value != "":
                raise ValueError("unqualified pair has outcome score")
            if int(r[f"{cohort}_matched_sites"]) < 0:
                raise ValueError("negative camera site support")
    return rows


def _solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Pivoted Gaussian elimination; disconnected graphs fail closed."""
    n = len(vector)
    if len(matrix) != n or any(len(a) != n for a in matrix):
        raise ValueError("non-square linear system")
    m = [list(map(float, matrix[i])) + [float(vector[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(m[row][col]))
        if abs(m[pivot][col]) < 1e-10:
            raise ValueError("nonidentified species gradient: disconnected support graph")
        m[col], m[pivot] = m[pivot], m[col]
        for row in range(col + 1, n):
            scale = m[row][col] / m[col][col]
            m[row][col] = 0.0
            for j in range(col + 1, n + 1):
                m[row][j] -= scale * m[col][j]
    result = [0.] * n
    for i in range(n-1, -1, -1):
        result[i] = (m[i][n] - math.fsum(m[i][j]*result[j] for j in range(i+1, n))) / m[i][i]
    return result


def _gradient_fit(edges: list[tuple[str, str]], shifts: list[float], taxa: list[str]) -> dict:
    n = len(taxa)
    if n < 2 or len(edges) != len(shifts):
        raise ValueError("invalid gradient inputs")
    index = {name: i for i, name in enumerate(taxa)}
    lap = [[1/n for _ in range(n)] for _ in range(n)]
    rhs = [0.] * n
    for (first, second), value in zip(edges, shifts, strict=True):
        if first not in index or second not in index or first == second or not math.isfinite(value):
            raise ValueError("invalid pair edge")
        a, b = index[first], index[second]
        lap[a][a] += 1
        lap[b][b] += 1
        lap[a][b] -= 1
        lap[b][a] -= 1
        rhs[a] += value
        rhs[b] -= value
    beta = _solve_linear(lap, rhs)
    centering = math.fsum(beta)/n
    beta = [v-centering for v in beta]
    predicted = [beta[index[a]]-beta[index[b]] for a,b in edges]
    residual = [value-p for value,p in zip(shifts,predicted,strict=True)]
    energy = math.fsum(v*v for v in shifts)
    if energy <= 0:
        raise ValueError("no contrast energy")
    rss = math.fsum(x*x for x in residual)
    return {
        "relative_species_score":dict(zip(taxa,beta,strict=True)),
        "predicted_pair_shifts":predicted,
        "energy_explained_relative_zero":1-rss/energy,
        "unexplained_energy_fraction":rss/energy,
        "RMSE_log_dry_wet":math.sqrt(rss/len(edges)),
    }


def _cycles(edges: list[tuple[str,str]], values: list[float], taxa: list[str]) -> dict:
    by_pair = dict(zip(edges,values,strict=True))
    closure = []
    for a,b,c in combinations(taxa,3):
        if (a,b) not in by_pair or (b,c) not in by_pair or (a,c) not in by_pair:
            continue
        closure.append(by_pair[(a,b)] + by_pair[(b,c)] - by_pair[(a,c)])
    return {
        "complete_taxon_triples": len(closure),
        "median_absolute_log_cycle_gap":median(abs(x) for x in closure) if closure else None,
        "max_absolute_log_cycle_gap":max(map(abs,closure)) if closure else None,
        "cycle_gaps_are_not_independent_observations":True,
    }


def analyze(rows: list[dict], *, check_expected: bool=False) -> dict:
    taxa = sorted({v for r in rows for v in (r['species_1'],r['species_2'])})
    shared = [r for r in rows if all(r[f'{cohort}_status']=='DESCRIPTIVE_ESTIMABLE' for cohort in COHORTS)]
    edges = [(r['species_1'],r['species_2']) for r in shared]
    active_taxa = sorted({v for e in edges for v in e})
    isolated_taxa = sorted(set(taxa)-set(active_taxa))
    if len(edges)<len(active_taxa)-1:
        raise ValueError('not enough shared edges for graph')
    shifts = {cohort:[float(r[f'{cohort}_log_dry_over_wet']) for r in shared] for cohort in COHORTS}
    fits = {cohort:_gradient_fit(edges,shifts[cohort],active_taxa) for cohort in COHORTS}
    cycles = {cohort:_cycles(edges,shifts[cohort],active_taxa) for cohort in COHORTS}
    truth=shifts['validation']; prediction=fits['discovery']['predicted_pair_shifts']
    baseline=math.fsum(v*v for v in truth)
    if baseline<=0:
        raise ValueError('validation zero-energy baseline undefined')
    transferred=1-math.fsum((v-p)**2 for v,p in zip(truth,prediction,strict=True))/baseline
    agreement=sum((a>0)==(b>0) for a,b in zip(shifts['discovery'],truth,strict=True))
    if check_expected and (len(rows),len(edges),len(active_taxa),len(isolated_taxa),agreement)!=(66,46,11,1,23):
        raise ValueError('original fixed-source support/statistics drift')
    return {
        'schema_version':1,
        'status':'E7_POSTRESULT_RELATIONAL_COHERENCE_DESCRIPTIVE',
        'source':{
            'original_E7_empirical_artifact_run_id':SOURCE_ARTIFACT_RUN,
            'original_E7_result_sha256':SOURCE_JSON_SHA256,
            'all_66_pair_table_sha256':PAIR_CSV_SHA256,
        },
        'support':{'original_taxa':len(taxa),'pair_universe':len(rows),'shared_estimated_pairs':len(edges),
                   'taxa_in_connected_shared_pair_graph':len(active_taxa),
                   'taxa_without_any_shared_eligible_edge':isolated_taxa,
                   'same_edge_support_in_both_splits':True},
        'method':{
            'contrast':'log((species1/species2 night/midday OR dry)/(wet))',
            'candidate_scalar_species_gradient':'delta_ij=beta_i-beta_j with sum(beta)=0',
            'fit':'equal-pair-weight Laplacian least-squares on exactly the common estimated 46 pairs',
            'score':'1 - residual_sum_squared / sum(observed_log_shift_squared); zero-shift null is baseline',
            'triangle_closure':'delta_ab + delta_bc - delta_ac; must equal zero for exact species-potential differences',
            'not_an_ecological_model_refit':True},
        'discovery':{**{k:v for k,v in fits['discovery'].items() if k!='predicted_pair_shifts'},
                     **cycles['discovery']},
        'validation':{**{k:v for k,v in fits['validation'].items() if k!='predicted_pair_shifts'},
                      **cycles['validation']},
        'out_of_period':{'discovery_species_gradient_on_validation_pair_edges_skill_vs_zero':transferred,
                         'pair_shift_sign_agreement':agreement,
                         'shared_pairs':len(edges)},
        'ecological_boundary':{
            'this_is_post_outcome_no_new_biological_response':True,
            'scalar_scores_are_descriptive_not_true_species_activity_traits':True,
            'pairwise_MH_uses_different_camera_subset_weights':True,
            'triangle_inconsistency_does_not_prove_interspecific_interaction':True,
            'geography_season_sensor_and_plant_visibility_not_separately_identified':True,
            'pair_edges_and_triangles_statistically_dependent_no_p_values':True,
            'source_detection_process_uncalibrated':True,
            'original_E4_scores_unchanged':True,'original_E5_G4_passed':False},
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--pair-table',type=Path,required=True)
    p.add_argument('--original-result',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    rows=load_pinned_pair_table(args.pair_table)
    if args.original_result:
        reconstructed=rows_from_frozen_source(args.original_result)
        if csv_bytes(reconstructed) != args.pair_table.read_bytes():
            raise ValueError('aggregate pair table does not exactly reproduce original source JSON')
    result=analyze(rows,check_expected=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'support':result['support'],
                      'discovery_energy':result['discovery']['energy_explained_relative_zero'],
                      'validation_energy':result['validation']['energy_explained_relative_zero'],
                      'out_of_period_skill':result['out_of_period']['discovery_species_gradient_on_validation_pair_edges_skill_vs_zero'],
                      'triangle_gaps':{c:result[c]['median_absolute_log_cycle_gap'] for c in COHORTS}},sort_keys=True))


if __name__=='__main__':
    main()
