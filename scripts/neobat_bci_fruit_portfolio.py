"""Public Dryad BCI annual mature-seed pilot against frozen NeoBat plant links.

Run only on the frozen 201-species publication and the immutable original
interaction CSV. Outputs an aggregate receipt, never publishes raw trap rows,
fine-scale sites, or animal locations. No bat response is modeled.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import random
import statistics
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen
from pathlib import Path

DOI = "doi:10.5061/dryad.4mw6m909j"
ENTRY = "https://datadryad.org/api/v2/datasets/" + quote(DOI, safe="")
NEOBAT_URL = ("https://raw.githubusercontent.com/gflorezm/NeoBat_Interactions/"
              "d25292d19be32a85a21c60384a3f2d818e8081de/"
              "Data/NeoBat_Interactions_Records.csv")
NEOBAT_SHA256 = "723198f850aa4ee7346122e71a3dd3eadaca176a65bfb87dc2a90f55f2acf10b"
ROSTER_SHA256 = "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
PRIMARY_BATS = (
    "Carollia perspicillata", "Artibeus lituratus", "Artibeus jamaicensis",
    "Sturnira lilium", "Artibeus planirostris", "Sturnira giannae",
    "Carollia brevicauda", "Artibeus phaeotis", "Sturnira parvidens",
    "Carollia castanea", "Chiroderma villosum", "Sturnira tildae",
    "Artibeus obscurus", "Platyrrhinus helleri", "Vampyressa thyone",
    "Rhinophylla pumilio", "Uroderma bilobatum", "Platyrrhinus lineatus",
    "Uroderma convexum", "Vampyriscus nymphaea", "Artibeus toltecus",
    "Artibeus watsoni", "Artibeus concolor", "Sturnira ludovici",
    "Artibeus gnomus", "Artibeus cinereus")
SIMULATIONS = 499
SEED = 20261124


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fetch_bytes(url, max_bytes):
    req = Request(url, headers={"User-Agent": "esdm-NeoBat-external-seed-portfolio/1.0",
                                "Accept": "*/*"})
    with urlopen(req, timeout=75) as response:
        require(response.status == 200, f"HTTP_{response.status}")
        final = urlparse(response.geturl())
        require(final.scheme == "https", "UNSAFE_REDIRECT_SCHEME")
        data = response.read(max_bytes + 1)
    require(len(data) <= max_bytes, "SOURCE_EXCEEDS_MAX_BYTES")
    return data


def dryad_link(meta, relation):
    link = meta.get("_links", {}).get(relation, {})
    require(isinstance(link, dict) and isinstance(link.get("href"), str),
            f"DRYAD_LINK_MISSING_{relation}")
    url = urljoin("https://datadryad.org", link["href"])
    parsed = urlparse(url)
    require(parsed.scheme == "https" and parsed.hostname == "datadryad.org"
            and parsed.path.startswith("/api/v2/"),
            f"DRYAD_LINK_OUTSIDE_OFFICIAL_API_{relation}")
    return url


def fetch_dryad_csv(fetch=fetch_bytes):
    dataset = json.loads(fetch(ENTRY, 2_000_000))
    require(str(dataset.get("identifier", "")).lower() == DOI,
            "DRYAD_DOI_MISMATCH")
    version = json.loads(fetch(dryad_link(dataset, "stash:version"), 2_000_000))
    files_url = dryad_link(version, "stash:files")
    selected = []
    total = None
    visited = set()
    while files_url:
        require(files_url not in visited and len(visited) < 10, "FILE_PAGINATION_INVALID")
        visited.add(files_url)
        page = json.loads(fetch(files_url, 2_000_000))
        if total is None:
            total = page.get("total")
        require(type(page.get("total")) is int and total == page["total"], "FILE_TOTAL_DRIFT")
        items = page.get("_embedded", {}).get("stash:files")
        require(isinstance(items, list), "FILES_NOT_AVAILABLE")
        selected.extend(f for f in items if f.get("path", "").split("/")[-1] == "fruit_drop.csv")
        next_link = page.get("_links", {}).get("next")
        files_url = None
        if next_link:
            files_url = dryad_link(page, "next")
    require(len(selected) == 1, "FRUIT_DROP_CSV_NOT_UNIQUE_IN_PUBLISHER_FILES")
    file = selected[0]
    url = dryad_link(file, "stash:download")
    payload = fetch(url, 3_000_000)
    require(len(payload) == file.get("size"), "DRYAD_FILE_BYTE_SIZE_MISMATCH")
    digest = hashlib.sha256(payload).hexdigest()
    if file.get("digestType") == "sha-256" and file.get("digest"):
        require(digest.lower() == str(file["digest"]).lower(), "DRYAD_PUBLISHER_DIGEST_MISMATCH")
    return payload, {
        "doi": DOI, "publisher": "Dryad", "dataset_id": dataset.get("id"),
        "version_id": version.get("id"), "version_number": version.get("versionNumber"),
        "file_path": file.get("path"), "file_size_bytes": len(payload),
        "file_sha256": digest, "publisher_digest_type": file.get("digestType"),
        "publisher_digest": file.get("digest"),
        "publisher_file_total": total,
    }


def parse_seeds(data):
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {"year", "sp4", "genus", "species", "abscised_seeds",
                "viable_seeds", "total_seeds", "sum_parts"}
    require(reader.fieldnames and required <= set(reader.fieldnames),
            "SEED_CSV_REQUIRED_COLUMNS_MISSING")
    samples = {}
    name_to_id = {}
    for idx, row in enumerate(reader):
        year = int(row["year"])
        require(1988 <= year <= 2018, "SEED_YEAR_OUT_OF_PUBLISHED_RANGE")
        spid = row["sp4"].strip()
        genus, specific = row["genus"].strip(), row["species"].strip()
        require(spid and genus and specific, "SEED_SPECIES_NAME_MISSING")
        binomial = (specific if specific.casefold().startswith(genus.casefold() + " ")
                    else genus + " " + specific.split()[0]).casefold()
        require(name_to_id.get(binomial, spid) == spid, "SEED_AMBIGUOUS_SPECIES")
        name_to_id[binomial] = spid
        counts = [float(row[key]) for key in ("abscised_seeds", "viable_seeds", "total_seeds")]
        require(all(math.isfinite(x) and x >= 0 for x in counts), "SEED_COUNTS_INVALID")
        require(abs(counts[0] + counts[1] - counts[2]) <=
                max(2, .01 * counts[2]), "SEED_ARITHMETIC_INVALID")
        key = (binomial, year)
        require(key not in samples, "DUPLICATE_SPECIES_YEAR")
        samples[key] = (counts[0], counts[1], counts[2])
    require(len(samples) == 5295, "DRYAD_PUBLISHED_5295_ROW_COUNT_DRIFT")
    require(len(name_to_id) == 201, "DRYAD_PUBLISHED_201_SPECIES_COUNT_DRIFT")
    return samples, name_to_id


def parse_bat_links(data, plant_roster):
    require(hashlib.sha256(data).hexdigest() == NEOBAT_SHA256, "NEOBAT_BLOB_SHA_DRIFT")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    records = list(csv.DictReader(io.StringIO(text)))
    require(len(records) == 2571, "NEOBAT_2571_SOURCE_ROWS_DRIFT")
    output = {bat: set() for bat in PRIMARY_BATS}
    for row in records:
        bat = row["CurrentBatSpecies"].strip()
        plant = row["CurrentPlantSpecies"].strip().casefold()
        if (row["Interaction"].strip().casefold() == "frugivory" and
            row["TrophicGuild"].strip().casefold() == "frugivore" and
            bat in output and plant in plant_roster):
            output[bat].add(plant)
    return output


def cv(vals):
    avg = statistics.mean(vals)
    return statistics.stdev(vals) / avg if len(vals) >= 2 and avg > 0 else None


def evaluate_bat(bat, plants, samples):
    years_per = {sp: {year for (taxon, year) in samples if taxon == sp} for sp in plants}
    years = set.intersection(*(v for v in years_per.values())) if years_per else set()
    desc = {"bat": bat, "source_linked_plants_with_BCI_records": len(plants),
            "plant_names": sorted(plants), "joint_years": len(years),
            "eligible_for_portfolio": len(plants) >= 3 and len(years) >= 10,
            "observed_portfolio_CV": None, "null_median_portfolio_CV": None,
            "observed_over_null_CV": None, "interpretation": "NOT_EVALUABLE"}
    if not desc["eligible_for_portfolio"]:
        return desc
    ys = sorted(years)
    columns = []
    for sp in sorted(plants):
        transformed = [math.log1p(samples[(sp, year)][1]) for year in ys]
        avg = statistics.mean(transformed)
        if avg <= 0:
            desc["eligible_for_portfolio"] = False
            desc["interpretation"] = "ZERO_LOG_MATURE_SEED_OUTPUT"
            return desc
        columns.append([x / avg for x in transformed])
    observed = [statistics.mean(values) for values in zip(*columns)]
    obs_cv = cv(observed)
    require(obs_cv is not None, "NONPOSITIVE_OBSERVED_PORTFOLIO")
    rng = random.Random(SEED)
    null = []
    for _ in range(SIMULATIONS):
        shifts = [rng.randrange(len(ys)) for _ in columns]
        series = [statistics.mean(
            col[(j + shifts[k]) % len(ys)] for k, col in enumerate(columns))
            for j in range(len(ys))]
        null.append(cv(series))
    nd = statistics.median(null)
    require(nd and nd > 0, "NULL_PORTFOLIO_CV_INVALID")
    desc.update({"observed_portfolio_CV": obs_cv,
                 "null_median_portfolio_CV": nd,
                 "observed_over_null_CV": obs_cv / nd,
                 "interpretation": ("MORE_COMPENSATORY_THAN_CIRCULAR_SHIFT_MEDIAN"
                                    if obs_cv < nd else
                                    "MORE_SYNCHRONOUS_THAN_CIRCULAR_SHIFT_MEDIAN"
                                    if obs_cv > nd else "EQUAL_TO_NULL_MEDIAN")})
    return desc


def run(seeds_csv, neo_csv, manifest):
    plants = {x.casefold() for x in manifest["plant_taxa"]}
    require(len(plants) == 106 and manifest["source_fixed106_sha256"] == ROSTER_SHA256,
            "FROZEN_106_INPUT_DRIFT")
    samples, species = parse_seeds(seeds_csv)
    links = parse_bat_links(neo_csv, plants)
    bci = set(species)
    matched = sorted(bci & plants)
    bat_results = [evaluate_bat(bat, links[bat] & bci, samples) for bat in PRIMARY_BATS]
    annual = []
    for sp in matched:
        entries = [row for (taxon, _), row in samples.items() if taxon == sp]
        abscised = sum(row[0] for row in entries)
        total = sum(row[2] for row in entries)
        annual.append({"plant": sp, "recorded_years": len(entries),
                       "premature_seed_fraction": abscised/total if total > 0 else None})
    return {"status": "EXPLORATORY_BCI_ORIGINAL_SEED_YIELD_AND_SOURCE_LINKS",
            "dataset_seed_year_rows": len(samples), "dataset_seed_species": len(species),
            "dataset_seed_year_range": [min(y for (_, y) in samples), max(y for (_, y) in samples)],
            "frozen_neobat_plant_roster": 106, "bci_matched_fixed_plants": len(matched),
            "matched_fixed_plant_names": matched,
            "neobat_bat_roster": len(PRIMARY_BATS),
            "candidate_bats_with_at_least_three_BCI_matched_plants":
                sum(z["source_linked_plants_with_BCI_records"] >= 3 for z in bat_results),
            "evaluable_bat_candidate_portfolios":
                sum(z["eligible_for_portfolio"] for z in bat_results),
            "candidate_bat_portfolios": bat_results,
            "plant_species_annual_output_support": annual,
            "analysis_semantics": {
                "seed_rain_not_ripe_fruit_or_bat_food_supply": True,
                "source_bat_diet_links_not_locally_verified_on_BCI": True,
                "missing_species_years_not_imputed_as_zeros": True,
                "circular_shift_median_not_a_p_value": True,
                "n_bat_profiles_not_independent_replicates": True,
                "bat_outcomes_not_observed": True,
                "trophic_M3_M1_gain_not_estimated": True}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"schema_version": 1, "source": DOI,
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "status": "SOURCE_NOT_EVALUABLE", "bat_model_fitted": False}
    try:
        seeds, src = fetch_dryad_csv()
        neobat = fetch_bytes(NEOBAT_URL, 2_000_000)
        data = run(seeds, neobat, json.loads(args.manifest.read_text(encoding="utf-8")))
        receipt.update(data)
        receipt["dryad_file"] = src
        receipt["neobat_original_csv_sha256"] = NEOBAT_SHA256
    except Exception as exc:
        receipt["status"] = "BCI_PUBLIC_SOURCE_OR_SCHEMA_STOP"
        receipt["error_type"] = type(exc).__name__
        receipt["error_code"] = str(exc)[:240]
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("BCI_FRUIT_PORTFOLIO", receipt["status"], receipt.get("error_code", ""), flush=True)
    return 0 if receipt["status"] == "EXPLORATORY_BCI_ORIGINAL_SEED_YIELD_AND_SOURCE_LINKS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
