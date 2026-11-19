#!/usr/bin/env python3
"""D1: frozen-before-response cross-country EDD prediction audit.

Never open animal images/sequence rows. Consumes only authors' published 2025
zone-level EDD summary (not independent known-passage detector calibration).
Folds always hold out an entire country, and do not tune predictors by response.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha1, sha256
from io import StringIO
import json
import math
from pathlib import Path
from statistics import mean, median, pstdev

SOURCE_COMMIT = "7a1d0f05d6a8042615083a0c8397a92afff75484"
SOURCE_GIT_BLOB = "64201f384e740031b4f3e9bbc116e3b2223d19dd"
SOURCE_CSV = "LOOCV_data 2025.csv"
SOURCE = "https://github.com/jnwiegers/predict_detection_zones"
DOI = "10.5061/dryad.gtht76j0c"
DESIGN = "docs/replication/D1_CROSSCOUNTRY_CAMERA_DETECTION_ZONE_FROZEN_DESIGN.md"
NEEDED = ("ID", "ref", "Country", "full.r", "ndet", "ct_brand", "body_mass", "ct_height", "T", "data.order")
ORDERS = frozenset(("carnivora", "primates", "rodentia", "ungulata"))
ALPHA = 10.0
PSEUDO_BRAND = 10.0
MIN_N = 40
MIN_COUNTRIES = 5
MIN_SCORE_COUNTRIES = 4
MIN_TRAIN = 30
MIN_TEST_PER_COUNTRY = 2


def finite(value: object) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def git_blob_sha1(data: bytes) -> str:
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def check_source(raw: bytes) -> dict:
    if git_blob_sha1(raw) != SOURCE_GIT_BLOB:
        raise ValueError("SOURCE_STOP: exact published Git blob SHA1 does not match")
    if len(raw) != 56728:
        raise ValueError("SOURCE_STOP: published 2025 EDD CSV byte length changed")
    return {"git_commit": SOURCE_COMMIT, "git_blob_sha1": SOURCE_GIT_BLOB,
            "sha256": sha256(raw).hexdigest(), "byte_length": len(raw), "data_file": SOURCE_CSV,
            "source_url": SOURCE, "doi": DOI}


def _seconds(value: object) -> float | None:
    if str(value or "").strip().casefold() == "contact":
        return 1500.0
    x = finite(value)
    return x if x is not None and x > 0 else None


def parse_zones(text: str) -> tuple[list[dict], dict]:
    reader = csv.DictReader(StringIO(text))
    if not set(NEEDED).issubset(set(reader.fieldnames or [])):
        raise ValueError("SCHEMA_STOP: published CSV required headers missing")
    seen: set[str] = set()
    eligible: list[dict] = []
    count = Counter()
    for record in reader:
        count["source_rows"] += 1
        key = str(record.get("ID") or "").strip()
        if not key or key in seen:
            raise ValueError("SCHEMA_STOP: source zone ID blank or duplicated")
        seen.add(key)
        order = str(record.get("data.order") or "").strip().casefold()
        if order not in ORDERS:
            count["excluded_not_fixed_mammal_order"] += 1
            continue
        country = str(record.get("Country") or "").strip()
        brand = str(record.get("ct_brand") or "").strip()
        full_r = finite(record.get("full.r"))
        ndet = finite(record.get("ndet"))
        mass = finite(record.get("body_mass"))
        height = finite(record.get("ct_height"))
        t = _seconds(record.get("T"))
        if (not country or not brand or full_r is None or full_r <= 0
            or ndet is None or ndet < 50 or ndet != int(ndet)
            or mass is None or mass <= 0 or height is None or height <= 0 or t is None):
            count["excluded_incomplete_or_low_detection"] += 1
            continue
        eligible.append({"country": country.casefold(), "brand": brand.casefold(),
                         "order": order, "target": math.log(full_r),
                         "num": (math.log(mass), math.log(height), math.log1p(t))})
        count["eligible_mammal_edd_zones"] += 1
    return eligible, dict(count)


def solve_linear(gram: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    if n < 1 or len(gram) != n or any(len(row) != n for row in gram):
        raise ValueError("MODEL_STOP: square Gram matrix required")
    a = [[float(v) for v in gram[i]] + [float(rhs[i])] for i in range(n)]
    for j in range(n):
        pivot = max(range(j, n), key=lambda i: abs(a[i][j]))
        if abs(a[pivot][j]) < 1e-12:
            raise ValueError("MODEL_STOP: singular Gram matrix")
        a[j], a[pivot] = a[pivot], a[j]
        z = a[j][j]
        a[j] = [v / z for v in a[j]]
        for i in range(n):
            if i == j:
                continue
            factor = a[i][j]
            a[i] = [v - factor * w for v, w in zip(a[i], a[j])]
    return [row[-1] for row in a]


def _training_scalers(training: list[dict]):
    values = [[r["num"][i] for r in training] for i in range(3)]
    return [(mean(v), pstdev(v)) for v in values]


def _model_vector(row: dict, scalers: list[tuple[float, float]], brands: list[str], orders: list[str]) -> list[float]:
    z = [1.0]
    for i, (m, sd) in enumerate(scalers):
        z.append((row["num"][i] - m) / sd if sd > 1e-12 else 0.0)
    z.extend(1.0 if row["brand"] == b else 0.0 for b in brands)
    z.extend(1.0 if row["order"] == o else 0.0 for o in orders)
    return z


def ridge_fit(train: list[dict]) -> dict:
    if len(train) < 2:
        raise ValueError("MODEL_STOP: fewer than two training zones")
    brands = sorted({r["brand"] for r in train})
    orders = sorted({r["order"] for r in train})
    scalers = _training_scalers(train)
    x = [_model_vector(r, scalers, brands, orders) for r in train]
    y = [r["target"] for r in train]
    p = len(x[0])
    gram = [[sum(row[i] * row[j] for row in x) + (ALPHA if i == j and i > 0 else 0.0)
             for j in range(p)] for i in range(p)]
    rhs = [sum(row[i] * target for row, target in zip(x, y)) for i in range(p)]
    coefficients = solve_linear(gram, rhs)
    return {"brands": brands, "orders": orders, "scalers": scalers, "coef": coefficients}


def predict_ridge(fit: dict, row: dict) -> float:
    return sum(c * x for c, x in zip(fit["coef"],
               _model_vector(row, fit["scalers"], fit["brands"], fit["orders"])))


def brand_fit(train: list[dict]) -> tuple[float, dict[str, tuple[int,float]]]:
    mu = mean(r["target"] for r in train)
    sums: dict[str, list[float]] = defaultdict(list)
    for r in train:
        sums[r["brand"]].append(r["target"])
    return mu, {brand: (len(xs), sum(xs)) for brand, xs in sums.items()}


def predict_brand(brand_model: tuple[float,dict], row: dict) -> float:
    mu, grouped = brand_model
    n, total = grouped.get(row["brand"], (0, 0.0))
    return (total + PSEUDO_BRAND * mu) / (n + PSEUDO_BRAND)


def score_fold(train: list[dict], test: list[dict]) -> dict:
    mu = mean(r["target"] for r in train)
    brand = brand_fit(train)
    full = ridge_fit(train)
    err = {"M0": [], "M1": [], "M2": []}
    new_brand = 0
    for row in test:
        new_brand += row["brand"] not in full["brands"]
        y = row["target"]
        err["M0"].append(abs(y - mu))
        err["M1"].append(abs(y - predict_brand(brand, row)))
        err["M2"].append(abs(y - predict_ridge(full, row)))
    return {"n": len(test), "errors": err, "unseen_brand_zones": new_brand}


def evaluate(zones: list[dict], quality: dict, provenance: dict) -> dict:
    country_counts = Counter(r["country"] for r in zones)
    countries = sorted(c for c, n in country_counts.items() if n >= MIN_TEST_PER_COUNTRY)
    base = {"schema_version": 1, "date": "2026-11-19", "source": provenance,
            "frozen_design": DESIGN, "quality": quality,
            "support": {"eligible_edd_zones": len(zones),
                        "countries_in_source": len(country_counts),
                        "scorable_heldout_countries": len(countries),
                        "scorable_heldout_zones": sum(country_counts[c] for c in countries)},
            "boundary": {"not_E5_G4": True,"not_independent_passage_denom": True,
                         "no_occupancy_or_abundance_estimate": True,
                         "no_eSDM_fit": True,"no_p_values_or_CI": True,
                         "no_source_response_rows_exported": True}}
    if len(zones) < MIN_N or len(country_counts) < MIN_COUNTRIES or len(countries) < MIN_SCORE_COUNTRIES or any(len(zones) - country_counts[c] < MIN_TRAIN for c in countries):
        base.update({"status":"INSUFFICIENT_COUNTRY_SUPPORT", "interpretation":"Predeclared complete-case/country support not met; no retuning"})
        return base
    all_errors = {key: [] for key in ("M0","M1","M2")}
    fold_summaries: list[dict] = []
    new_brand = 0
    for country in countries:
        train = [r for r in zones if r["country"] != country]
        test = [r for r in zones if r["country"] == country]
        f = score_fold(train, test)
        new_brand += f["unseen_brand_zones"]
        for name in all_errors:
            all_errors[name].extend(f["errors"][name])
        summaries = {name:mean(f["errors"][name]) for name in all_errors}
        fold_summaries.append({"country_fold_ordinal":len(fold_summaries)+1,
                               "heldout_zone_count":len(test),
                               "mae_log_meters":summaries,
                               "gain_M0_minus_M2":summaries["M0"] - summaries["M2"],
                               "gain_M1_minus_M2":summaries["M1"] - summaries["M2"],
                               "unseen_brand_zones":f["unseen_brand_zones"]})
    pooled = {name:mean(errs) for name,errs in all_errors.items()}
    gain = pooled["M0"]-pooled["M2"]
    positive_folds = sum(f["gain_M0_minus_M2"]>0 for f in fold_summaries)
    success = gain >=0.05 and positive_folds/len(countries)>=.6
    base.update({"status":"D1_DESCRIPTIVE_COUNTRY_TRANSFER_POSITIVE" if success else "D1_NO_USEFUL_INCREMENTAL_COUNTRY_TRANSFER",
                 "primary": {"pooled_MAE_log_edd": pooled,"pooled_gain_M0_minus_M2":gain,
                             "per_country_positive_count":positive_folds,
                             "per_country_scored_count":len(countries),
                             "predeclared_positive_rule_passed":success,
                             "country_balanced_mean_gain":mean(f["gain_M0_minus_M2"] for f in fold_summaries)},
                 "secondary":{"pooled_gain_M0_minus_M1":pooled["M0"]-pooled["M1"],
                              "pooled_gain_M1_minus_M2":pooled["M1"]-pooled["M2"],
                              "unseen_brand_heldout_zones":new_brand,
                              "country_fold_summaries_without_country_names":fold_summaries}})
    return base


def analyze_raw(raw: bytes) -> dict:
    source = check_source(raw)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ValueError("SCHEMA_STOP: EDD CSV not UTF-8") from e
    zones, quality = parse_zones(text)
    return evaluate(zones, quality, source)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args = parser.parse_args()
    try:
        result = analyze_raw(args.input.read_bytes())
    except (ValueError, OSError) as exc:
        msg = str(exc)
        status = msg.split(":", 1)[0]
        if status not in ("SCHEMA_STOP", "SOURCE_STOP", "MODEL_STOP"):
            status = "MODEL_STOP"
        result = {"schema_version":1,"status":status,"error":msg,
                  "frozen_design":DESIGN,"source_response_rows_exported":False,
                  "model_fitted":False}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"support":result.get("support"),
                      "primary_gain":result.get("primary",{}).get("pooled_gain_M0_minus_M2")},sort_keys=True))


if __name__ == "__main__":
    main()
