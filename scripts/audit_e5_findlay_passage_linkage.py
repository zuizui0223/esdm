#!/usr/bin/env python3
"""Post-outcome Findlay record-linkage QC, without re-estimating biological effects.

Two exact Git-blob-pinned CSVs are opened in one *explicitly exploratory* route.
Only a prespecified identity/fingerprint/trigger-consistency audit is permitted.
Raw rows, IDs, fingerprints and event values are never emitted.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from urllib.request import Request, urlopen

EXPECTED_ID="e5-findlay-postoutcome-record-linkage-forensic-v1"
SOURCE_COMMIT="abc72f535bb59ebed202fb7acca852fc1647e97a"
SOURCE_REPO="melaniefindlay/CT-Detection"
SOURCE_FILES=("TRIGGER_FOX_BADGER.csv","REGISTRATION_FOX_BADGER.csv")
MANDATORY=("SPECIES","CT.POS","ORIENT","DIST")
OPTIONAL=("GAIT.1","LOIT","AIR")
PASS_IDS=("PASS.ID","PASSAGE.ID","EVENT.ID","RECORD.ID","CCTV.PASS.ID",
          "OBSERVATION.ID","PASS_ID","PASSAGE_ID","EVENT_ID","RECORD_ID")


def blob_sha(blob:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()


def pinned_download(spec:dict)->bytes:
    if spec["name"] not in SOURCE_FILES:
        raise ValueError("forbidden source filename")
    url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{spec['name']}"
    req=Request(url,headers={"User-Agent":"esdm-Findlay-identity-QC/1"})
    with urlopen(req,timeout=90) as stream:
        blob=stream.read(int(spec["bytes"])+1)
    if len(blob)!=spec["bytes"] or blob_sha(blob)!=spec["sha"]:
        raise ValueError("Git blob/byte size drift")
    return blob


def parse_csv(blob:bytes)->tuple[list[str],list[dict[str,str]]]:
    reader=csv.DictReader(io.StringIO(blob.decode("utf-8-sig"),newline=""))
    headers=reader.fieldnames or []
    if len(set(headers))!=len(headers) or not headers:
        raise ValueError("duplicate or empty CSV headers")
    rows=list(reader)
    if any(None in r or any(x is None for x in r.values()) for r in rows):
        raise ValueError("malformed CSV row")
    return headers,rows


def canon(x:str,field:str)->str:
    v=x.strip()
    if field=="DIST":
        try:
            n=float(v)
            if math.isfinite(n):
                return format(n,".12g")
        except ValueError:
            pass
    return v.upper()


def signature(row:dict[str,str],fields:tuple[str,...])->tuple[str,...]:
    return tuple(canon(row[k],k) for k in fields)


def binner(row:dict[str,str])->str|None:
    if row["SPECIES"].strip().upper() not in ("BADGER","FOX"):
        return None
    if row["ORIENT"].strip().upper()!="L":
        return None
    try:
        d=float(row["DIST"])
    except (ValueError,TypeError):
        return None
    if not math.isfinite(d) or d<=0:
        return None
    return "near_le_1m" if d<=1 else ("mid_1_to_3m" if d<=3 else "far_gt_3m")


def audit(contract:dict,source:dict[str,bytes])->dict:
    if contract.get("contract_id")!=EXPECTED_ID:
        raise ValueError("unexpected contract")
    if contract.get("status")!="FROZEN_POSTOUTCOME_EXPLORATORY_NOT_AUTHORIZED":
        raise ValueError("not frozen")
    if contract.get("source",{}).get("commit")!=SOURCE_COMMIT:
        raise ValueError("source commit drift")
    specs=contract["source"]["files"]
    if tuple(s["name"] for s in specs)!=SOURCE_FILES:
        raise ValueError("file order drift")
    g=contract["predeclared_identity_fields"]
    if tuple(g["required_shared_nonoutcome_columns"])!=MANDATORY:
        raise ValueError("mandatory identity columns drift")
    if tuple(g["optional_shared_nonoutcome_columns"])!=OPTIONAL:
        raise ValueError("optional identity columns drift")
    if tuple(g["permitted_unique_pass_key_column_names"])!=PASS_IDS:
        raise ValueError("pass-key whitelist drift")
    fw=contract["firewall"]
    if not(fw["no_original_one_shot_rerun"] and fw["original_E5_G4_remains_unpassed"]
           and fw["new_QC_is_exploratory_only"]):
        raise ValueError("scientific boundary drift")
    parsed={}
    for spec in specs:
        name=spec["name"]
        blob=source[name]
        if len(blob)!=spec["bytes"] or blob_sha(blob)!=spec["sha"]:
            raise ValueError("pinned CSV source mismatch")
        parsed[name]=parse_csv(blob)
    th,tr=parsed[SOURCE_FILES[0]]
    rh,rr=parsed[SOURCE_FILES[1]]
    for header in (th,rh):
        if any(k not in header for k in MANDATORY+("TRIGGER",)):
            raise ValueError("mandatory linkage fields absent")
    if "CAPTURE" not in rh:
        raise ValueError("registration result missing CAPTURE")
    used=MANDATORY+tuple(k for k in OPTIONAL if k in th and k in rh)
    ts=[signature(row,used) for row in tr]
    rs=[signature(row,used) for row in rr]
    tc,rc=Counter(ts),Counter(rs)
    allkeys=set(tc)|set(rc)
    unique_pairs=sum(1 for k in allkeys if tc[k]==1 and rc[k]==1)
    unique_row_pairs=unique_pairs
    ambiguous_pairs=sum(min(tc[k],rc[k]) for k in allkeys if tc[k]>1 or rc[k]>1)
    excess_a=sum(max(tc[k]-rc[k],0) for k in allkeys)
    excess_b=sum(max(rc[k]-tc[k],0) for k in allkeys)
    order_matched=sum(a==b for a,b in zip(ts,rs))
    same_row_count=len(tr)==len(rr)
    order_exact=same_row_count and order_matched==len(tr)
    trigger_eq=sum(
        tr[i]["TRIGGER"].strip()==rr[i]["TRIGGER"].strip()
        for i in range(min(len(tr),len(rr))) if ts[i]==rs[i]
    )
    # Candidate stable pass identifier must be explicitly named and unique in BOTH.
    candidates=[]
    for name in PASS_IDS:
        if name not in th or name not in rh:
            continue
        aid=[x[name].strip() for x in tr]
        bid=[x[name].strip() for x in rr]
        nonblank=all(aid) and all(bid)
        uniq=nonblank and len(set(aid))==len(aid) and len(set(bid))==len(bid)
        common=uniq and set(aid)==set(bid)
        if common:
            map_b={x[name].strip():x for x in rr}
            stable=sum(
                signature(a,used)==signature(map_b[a[name].strip()],used)
                and a["TRIGGER"].strip()==map_b[a[name].strip()]["TRIGGER"].strip()
                for a in tr
            )
        else:
            stable=0
        candidates.append({"column":name,"unique_both":bool(uniq),"matching_identifier_sets":bool(common),
                           "fully_consistent_pass_records":int(stable),
                           "internal_pass_identity_linkage":bool(common and stable==len(tr))})
    verified_id=bool(candidates and all(z["internal_pass_identity_linkage"] for z in candidates))
    # If no unique stable pass ID, any matched row order/fingerprint is evidence
    # of source similarity but NOT an independently verified passage-level link.
    status=("INTERNALLY_LINKED_BY_UNIQUE_PASS_ID" if verified_id else
            "ROW_ORDER_AGREEMENT_NO_PASS_ID" if order_exact and trigger_eq==len(tr) else
            "FINGERPRINT_SUPPORT_WITHOUT_PASS_ID" if unique_pairs>0 else
            "NO_RECORD_LEVEL_LINKAGE_EVIDENCE")
    # Existing FOX/BADGER cohort bin names only; never compute a new rate or contrast.
    triggered_alignment=[]
    if verified_id:
        key=candidates[0]["column"]
        reg_by_id={r[key].strip():r for r in rr}
        cells=Counter()
        for a in tr:
            cell=binner(a)
            if cell is None:
                continue
            if a["TRIGGER"].strip()=="1":
                src=(a["SPECIES"].strip().upper(),cell)
                c=reg_by_id[a[key].strip()]["CAPTURE"].strip()
                cells[(src,"cctv_triggered")] += 1
                if c not in ("0","1"):
                    cells[(src,"registration_missing_capture")] += 1
        for species in ("BADGER","FOX"):
            for binname in ("near_le_1m","mid_1_to_3m","far_gt_3m"):
                triggered_alignment.append({
                  "species":species,"distance_bin":binname,
                  "linked_reference_triggered":cells[((species,binname),"cctv_triggered")],
                  "linked_missing_capture":cells[((species,binname),"registration_missing_capture")]
                })
    return {
      "schema_version":1,
      "route_id":EXPECTED_ID,
      "status":status,
      "source_commit":SOURCE_COMMIT,
      "input_row_counts":{"trigger":len(tr),"registration":len(rr)},
      "identity_fields_used":list(used),
      "stable_pass_ID_candidates":candidates,
      "row_order":{"identical_row_count":same_row_count,
                   "matching_shared_covariate_signature_positions":order_matched,
                   "matching_TRIGGER_values_at_signature_equal_positions":trigger_eq,
                   "all_shared_covariate_rows_correspond_in_order":order_exact},
      "unordered_covariate_fingerprint":{
        "uniquely_corresponding_signature_pairs":unique_row_pairs,
        "matched_but_ambiguous_duplicate_fingerprint_rows":ambiguous_pairs,
        "trigger_side_unmatched_rows":excess_a,
        "registration_side_unmatched_rows":excess_b
      },
      "linked_stage_missingness_if_true_unique_pass_ID":triggered_alignment,
      "decision":{
        "internally_identified_passage_identity_in_source":verified_id,
        "row_order_not_independent_identity_proof":True,
        "covariate_fingerprint_not_independent_identity_proof":True,
        "original_FOX_stage_effect_unchanged":True,
        "original_BADGER_count_mismatch_not_repaired":True,
        "original_Findlay_one_shot_rerun":False,
        "original_G4_passed":False,
        "original_E5_qualified":False,
        "new_biological_result_fitted":False,
        "CCTV_known_passage_diel_calibration_proven":False,
        "original_stage_receipt_must_not_be_reclassified":True
      },
      "response_firewall":{
        "two_pinned_biological_CSVs_opened_under_separate_exploratory_route":2,
        "raw_passage_ID_values_or_fingerprints_uploaded":False,
        "raw_rows_or_date_values_uploaded":False,
        "new_rates_or_effect_directions_computed":False,
        "model_fits":0
      }
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    inputs={spec["name"]:pinned_download(spec) for spec in contract["source"]["files"]}
    out=audit(contract,inputs)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
