"""Offline Dryad v2 HAL source metadata and integrity regressions, no biological data."""
from __future__ import annotations
import copy
import unittest

from scripts import neobat_BCI_dryad_original_file_manifest as m

VERSION="https://datadryad.org/api/v2/versions/1234"
FILES="https://datadryad.org/api/v2/versions/1234/files"


def responses():
    return {
       m.ENTRY:{
          "identifier":m.DOI,"id":12,
          "title":"Independent BCI original field tree plots",
          "storageSize":3500,
          "_links":{"stash:version":{"href":"/api/v2/versions/1234"}}
       },
       VERSION:{
          "id":1234,"versionNumber":2,"versionStatus":"published",
          "_links":{"stash:files":{"href":"/api/v2/versions/1234/files"}}
       },
       FILES:{
          "total":2,"count":2,
          "_embedded":{"stash:files":[
              {"id":100,"path":"plot_header.csv","size":500,
               "mimeType":"text/csv","digestType":"sha-256","digest":"a"*64},
              {"id":101,"path":"tree_counts.csv","size":3000,
               "mimeType":"text/csv","digestType":"sha-256","digest":"b"*64},
          ]}
       }
    }


class TestBCIOriginalDryadMetadata(unittest.TestCase):
    def test_exact_offline_original_dataset_version_and_file_metadata(self):
        obj=responses()
        result=m.audit(fetch=lambda url:obj[url])
        self.assertEqual(result["status"],m.SOURCE_PASS)
        self.assertEqual(result["current_version_files_reported"],2)
        self.assertEqual(result["listed_version_file_bytes"],3500)
        self.assertTrue(result["listed_bytes_match_dataset_storage_size"])
        self.assertTrue(result["source_Dryad_API_only_no_original_files_downloaded"])
        self.assertFalse(result["biological_plant_rows_or_plot_coordinates_read"])

    def test_off_host_or_unapproved_api_path_fails_closed(self):
        for url in ("http://datadryad.org/api/v2/versions/22",
                    "https://example.com/api/v2/versions/22",
                    "https://datadryad.org/private/download/sensitive.csv",
                    "https://datadryad.org.evil.com/api/v2/files"):
            with self.assertRaises(ValueError):
                m.exact_api_url(url)
        self.assertEqual(m.exact_api_url("/api/v2/versions/1234"),VERSION)

    def test_changed_dataset_DOI_fails_before_file_response(self):
        d=responses()
        d[m.ENTRY]["identifier"]="doi:10.5061/dryad.other"
        with self.assertRaisesRegex(RuntimeError,"DOI_MISMATCH"):
            m.audit(fetch=lambda url:d[url])

    def test_missing_file_pagination_exhaustion_fails_closed(self):
        d=responses()
        d[FILES]["total"]=3
        with self.assertRaisesRegex(RuntimeError,"TOTAL_FILES_MISMATCH"):
            m.audit(fetch=lambda url:d[url])

    def test_duplicate_file_id_is_source_failure(self):
        d=responses()
        d[FILES]["_embedded"]["stash:files"][1]["id"]=100
        with self.assertRaisesRegex(RuntimeError,"DUPLICATE_PAGINATED_FILE_ID"):
            m.audit(fetch=lambda url:d[url])

    def test_storage_size_inconsistency_is_not_silently_accepted(self):
        d=responses()
        d[m.ENTRY]["storageSize"]=3501
        with self.assertRaisesRegex(RuntimeError,"STORAGE_SIZE_DRIFT"):
            m.audit(fetch=lambda url:d[url])


if __name__=="__main__":
    unittest.main()
