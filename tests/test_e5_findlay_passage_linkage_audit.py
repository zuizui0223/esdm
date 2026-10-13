from __future__ import annotations
import copy,csv,io,json
from pathlib import Path
import pytest
from scripts.audit_e5_findlay_passage_linkage import audit,blob_sha
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs/replication/E5_FINDLAY_PASSAGE_LINKAGE_AUDIT_CONTRACT.json"


def make_data(key:bool=False,reverse:bool=False):
    ids=["a","b","c","d"]
    headers=["SPECIES","CT.POS","ORIENT","DIST","GAIT.1","LOIT","AIR","TRIGGER"]
    if key:headers+=["PASS.ID"]
    a=[["FOX","CT1","L","0.5","W","0","12","1"],
       ["FOX","CT2","L","4","R","0","11","1"],
       ["BADGER","CT3","L","4","W","1","10","1"],
       ["FOX","CT4","L","2","W","0","14","0"]]
    if key:
        a=[row+[ids[i]] for i,row in enumerate(a)]
    b=[dict(zip(headers,row),CAPTURE=str(int(i%2==0))) for i,row in enumerate(a)]
    if reverse:b=b[::-1]
    def output(rows,fields):
        fh=io.StringIO(newline="")
        w=csv.DictWriter(fh,fieldnames=fields)
        w.writeheader();w.writerows(rows)
        return fh.getvalue().encode("utf-8")
    aa=output([dict(zip(headers,row)) for row in a],headers)
    bb=output(b,headers+["CAPTURE"])
    c=copy.deepcopy(json.loads(CONTRACT.read_text(encoding="utf-8")))
    for spec,buf in zip(c["source"]["files"],(aa,bb)):
        spec["bytes"]=len(buf)
        spec["sha"]=blob_sha(buf)
    return c,{c["source"]["files"][0]["name"]:aa,c["source"]["files"][1]["name"]:bb}


def test_row_order_equal_without_pass_id_never_claims_unique_identity():
    c,s=make_data()
    z=audit(c,s)
    assert z["status"]=="ROW_ORDER_AGREEMENT_NO_PASS_ID"
    assert z["row_order"]["all_shared_covariate_rows_correspond_in_order"] is True
    assert z["unordered_covariate_fingerprint"]["uniquely_corresponding_signature_pairs"]==4
    assert z["decision"]["internally_identified_passage_identity_in_source"] is False
    assert z["linked_stage_missingness_if_true_unique_pass_ID"]==[]


def test_explicit_unique_pass_key_allows_internal_cohort_audit_without_effects():
    c,s=make_data(key=True,reverse=True)
    z=audit(c,s)
    assert z["status"]=="INTERNALLY_LINKED_BY_UNIQUE_PASS_ID"
    assert z["decision"]["internally_identified_passage_identity_in_source"] is True
    assert z["row_order"]["all_shared_covariate_rows_correspond_in_order"] is False
    assert z["decision"]["new_biological_result_fitted"] is False
    assert sum(x["linked_reference_triggered"] for x in z["linked_stage_missingness_if_true_unique_pass_ID"])==3


def test_missing_pass_key_and_noncorresponding_order_does_not_assert_linkage():
    c,s=make_data(reverse=True)
    z=audit(c,s)
    assert z["status"]=="FINGERPRINT_SUPPORT_WITHOUT_PASS_ID"
    assert z["decision"]["internally_identified_passage_identity_in_source"] is False


def test_frozen_contract_and_no_E5_promotion():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert c["status"]=="FROZEN_POSTOUTCOME_EXPLORATORY_NOT_AUTHORIZED"
    assert c["source"]["commit"]=="abc72f535bb59ebed202fb7acca852fc1647e97a"
    assert c["firewall"]["original_stage_counts_and_compensation_index_unchanged"] is True
    assert c["firewall"]["original_E5_G4_remains_unpassed"] is True
    assert c["firewall"]["original_E5_qualified_count_remains_zero"] is True
    assert c["firewall"]["new_QC_is_exploratory_only"] is True


def test_unpinned_bytes_rejected():
    c,s=make_data()
    c["source"]["files"][0]["sha"]="0"*40
    with pytest.raises(ValueError,match="pinned CSV source mismatch"):
        audit(c,s)
