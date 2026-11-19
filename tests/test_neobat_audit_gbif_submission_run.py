"""Offline unit tests: no GitHub network, no GBIF credential or POST request."""
import unittest
from scripts import neobat_audit_gbif_submission_run as audit

def mocked_api(p):
    if "workflows/" in p and "/runs?" in p:
        return {"workflow_runs":[
            {"id":100,"head_sha":"different","event":"push","conclusion":"success"},
            {"id":123456,"head_sha":audit.MARKER_SHA,"event":"push",
             "status":"completed","conclusion":"failure","run_attempt":1,
             "created_at":"2026-11-19T00:00:00Z","updated_at":"2026-11-19T00:01:00Z"}
        ]}
    if p=="/actions/runs/123456/jobs?per_page=100":
        return {"jobs":[{
            "name":"request_authenticated_gbif_downloads","status":"completed",
            "conclusion":"failure","steps":[{"name":"Submit exactly one bat and one plant download to GBIF",
                                             "status":"completed","conclusion":"failure"}]}]}
    if p=="/actions/runs/123456/artifacts?per_page=100":
        return {"artifacts":[{"name":"neobat-first-gbif-doi-download-requests",
                              "id":987,"size_in_bytes":1234,"expired":False}]}
    raise ValueError("unexpected URL:"+p)

class TestReadOnlyAudit(unittest.TestCase):
    def test_filters_exact_marker_and_keeps_only_safe_metadata(self):
        r=audit.audit(mocked_api)
        self.assertEqual(r["status"],"RUN_FOUND")
        self.assertEqual(r["target_runs_found"],1)
        self.assertEqual(r["run_findings"][0]["run_id"],123456)
        self.assertEqual(r["run_findings"][0]["jobs"][0]["conclusion"],"failure")
        self.assertEqual(r["run_findings"][0]["artifacts"][0]["id"],987)
        self.assertTrue(r["no_credentials_fetched"])
        self.assertFalse(r["GBIF_POST_retried"])
        self.assertNotIn("log",str(r))

    def test_missing_run_is_distinct_from_failed_run(self):
        r=audit.audit(lambda p: {"workflow_runs":[]})
        self.assertEqual(r["status"],"NO_PUSH_RUN_FOR_EXACT_MARKER")
        self.assertEqual(r["target_runs_found"],0)

if __name__=="__main__":
    unittest.main()
