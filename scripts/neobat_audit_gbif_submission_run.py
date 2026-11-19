"""Read-only GitHub Actions audit for the single NeoBat GBIF DOI submit marker.

Never dispatches a workflow, never calls the GBIF POST endpoint, and never
prints or fetches secret values. Only public run/job/step status and artifact
names are retained. Intended for a one-shot PR-triggered observability audit.
"""
from __future__ import annotations
import argparse, json, os, pathlib, sys
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

OWNER="zuizui0223"
REPO="esdm"
WORKFLOW="neobat-gbif-doi-download-once.yml"
MARKER_SHA="37c1c92ef37225c8898ed8f63a4333263f424695"
BRANCH="design/neobat-trophic-sdm-phase1-20261119"
BASE="https://api.github.com/repos/"+OWNER+"/"+REPO

def api_get(path,token):
    req=Request(BASE+path,headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"esdm-neobat-download-run-inspector"})
    with urlopen(req,timeout=30) as f:
        return json.loads(f.read().decode("utf-8"))

def audit(getter, marker_sha=MARKER_SHA, workflow_file=WORKFLOW, workflow_name="NeoBat DOI-backed GBIF bat and plant occurrence downloads (single authorization)"):
    # The repository-level endpoint resolves an exact head SHA even when
    # the named workflow file exists only on a non-default branch.
    path=("/actions/runs?head_sha="+quote(marker_sha,safe="")
          +"&event=push&per_page=100")
    payload=getter(path)
    runs=payload.get("workflow_runs",[])
    target=[r for r in runs if r.get("head_sha")==marker_sha and
            r.get("event")=="push" and
            (r.get("name")==workflow_name
             or r.get("path","").endswith("/"+workflow_file))]
    result={
        "schema_version":1,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "target_marker_sha":marker_sha,
        "target_workflow_name":workflow_file,
        "target_branch":BRANCH,
        "mode":"READ_ONLY_GITHUB_RUN_METADATA",
        "GBIF_POST_retried":False,
        "no_credentials_fetched":True,
        "target_runs_found":len(target),
        "run_findings":[]
    }
    for r in target:
        runid=r["id"]
        jj=getter("/actions/runs/"+str(runid)+"/jobs?per_page=100")
        aa=getter("/actions/runs/"+str(runid)+"/artifacts?per_page=100")
        result["run_findings"].append({
            "run_id":runid,
            "run_attempt":r.get("run_attempt"),
            "event":r.get("event"),
            "status":r.get("status"),
            "conclusion":r.get("conclusion"),
            "created_at":r.get("created_at"),
            "updated_at":r.get("updated_at"),
            "jobs":[{
                "name":j.get("name"),
                "status":j.get("status"),
                "conclusion":j.get("conclusion"),
                "steps":[{"name":s.get("name"),"status":s.get("status"),
                          "conclusion":s.get("conclusion")}
                         for s in j.get("steps",[])]
            } for j in jj.get("jobs",[])],
            "artifacts":[{
                "id":a.get("id"),
                "name":a.get("name"),
                "size_in_bytes":a.get("size_in_bytes"),
                "expired":a.get("expired")
            } for a in aa.get("artifacts",[])]
        })
    result["status"]="RUN_FOUND" if target else "NO_PUSH_RUN_FOR_EXACT_MARKER"
    return result

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--out",default="docs/replication/neobat/gbif_one_shot_action_audit.json")
    pa.add_argument("--marker-sha",default=MARKER_SHA)
    pa.add_argument("--workflow-file",default=WORKFLOW)
    pa.add_argument("--workflow-name",default="NeoBat DOI-backed GBIF bat and plant occurrence downloads (single authorization)")
    args=pa.parse_args()
    dest=pathlib.Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    token=os.environ.get("GITHUB_TOKEN","")
    try:
        if not token: raise RuntimeError("GITHUB_TOKEN_MISSING")
        x=audit(lambda path: api_get(path,token),marker_sha=args.marker_sha,
                workflow_file=args.workflow_file,workflow_name=args.workflow_name)
    except Exception as exc:
        x={"schema_version":1,"status":"ACTION_AUDIT_API_STOP",
           "error_type":type(exc).__name__,
           "GBIF_POST_retried":False,"no_credentials_fetched":True}
    dest.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_GBIF_ACTION_AUDIT",x["status"],
          "target_runs_found",x.get("target_runs_found",0),flush=True)
    return 0 if x["status"]=="RUN_FOUND" else 3

if __name__=="__main__":
    sys.exit(main())
