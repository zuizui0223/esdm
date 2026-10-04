#!/usr/bin/env python3
"""Response-blind schema precheck for the Kays et al. 2020 eMammal data dictionary."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


EXPECTED_CONTRACT_ID = "e5-kays41-data-dictionary-response-blind-v1"


def _plain_rtf(raw: bytes) -> str:
    text = raw.decode("latin-1", errors="strict")
    if not text.lstrip().startswith("{\\rtf"):
        raise ValueError("dictionary is not RTF")
    # Decode simple RTF hex escapes, then discard control words/groups. This is used
    # only for a schema dictionary, never for a biological response file.
    text = re.sub(
        r"\\'([0-9a-fA-F]{2})",
        lambda m: bytes.fromhex(m.group(1)).decode("latin-1"),
        text,
    )
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", text)
    text = text.replace("\\{", "{").replace("\\}", "}").replace("\\\\", "\\")
    text = text.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", text).strip()


def _concepts(text: str) -> dict[str, bool]:
    low = text.casefold()
    patterns = {
        "deployment_identifier": (
            r"deployment[_ ]?id", r"deployment identifier", r"deployment"
        ),
        "deployment_start_or_begin": (
            r"deployment[_ ]?(start|begin)", r"start[_ ]?date", r"begin[_ ]?date"
        ),
        "deployment_end_or_retrieval": (
            r"deployment[_ ]?end", r"end[_ ]?date", r"retrieval[_ ]?date"
        ),
        "study_or_project_identifier": (
            r"study[_ ]?id", r"project[_ ]?id", r"study[_ ]?area", r"project"
        ),
        "site_or_location_identifier": (
            r"site[_ ]?id", r"location[_ ]?id", r"camera[_ ]?site", r"site"
        ),
        "camera_model": (
            r"camera[_ ]?model", r"model of camera", r"camera make"
        ),
        "camera_or_device_identifier": (
            r"camera[_ ]?id", r"device[_ ]?id", r"camera identifier"
        ),
        "observation_date": (
            r"photo[_ ]?date", r"observation[_ ]?date", r"date"
        ),
        "observation_time": (
            r"photo[_ ]?time", r"observation[_ ]?time", r"time"
        ),
        "sampling_occasion_or_sequence": (
            r"occasion", r"sequence[_ ]?id", r"sampling occasion"
        ),
        "latitude_longitude": (
            r"latitude", r"longitude", r"utm"
        ),
    }
    return {
        key: any(re.search(pattern, low) for pattern in values)
        for key, values in patterns.items()
    }


def precheck(dictionary_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Kays41 dictionary contract")

    fw = contract["response_firewall"]
    forbidden_true = (
        "any_response_file_download_authorized",
        "seasonal_zip_open_authorized",
        "spatial_raw_detections_open_authorized",
        "temporal_detection_rate_open_authorized",
        "temporal_species_zip_open_authorized",
        "focal_species_values_authorized",
        "detection_rows_authorized",
        "model_fitting_authorized",
    )
    if any(fw.get(key) is not False for key in forbidden_true):
        raise ValueError("response firewall drifted")

    raw = dictionary_path.read_bytes()
    if len(raw) > 128 * 1024:
        raise ValueError("dictionary unexpectedly large")
    plain = _plain_rtf(raw)
    concepts = _concepts(plain)

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "kays41_emammal_team_2020",
        "precheck_id": "e5-kays41-data-dictionary-result-v1",
        "status": "E5_RESPONSE_BLIND_DICTIONARY_PRECHECK",
        "source": {
            "dataset_doi": contract["source"]["dataset_doi"],
            "dryad_file_id": contract["source"]["dryad_file_id"],
            "dictionary_file": contract["source"]["dictionary_file"],
            "dictionary_sha256": hashlib.sha256(raw).hexdigest(),
            "dictionary_byte_size": len(raw),
        },
        "schema_concepts": concepts,
        "response_boundary": {
            "dictionary_files_read": 1,
            "response_files_downloaded": 0,
            "response_files_opened": 0,
            "detection_rows_read": 0,
            "species_values_read": 0,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "separate_child_contract_required_before_any_response_file_header_or_row": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = precheck(args.dictionary, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
