"""Synthetic-only tests: no GBIF response records or network source needed."""
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "scripts" / "neobat_gbif_metadata_preflight.py"
spec = importlib.util.spec_from_file_location("neobat_preflight", P)
pre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pre)


def fixture(primary="Frugivore"):
    records = [
        dict(SiteCode="S1", RefCode="R1", CurrentBatSpecies="Carollia perspicillata",
             CurrentPlantSpecies="Ficus insipida", Interaction="Frugivory", TrophicGuild=primary),
        dict(SiteCode="S2", RefCode="R2", CurrentBatSpecies="Carollia perspicillata",
             CurrentPlantSpecies="Piper aduncum", Interaction="Frugivory", TrophicGuild=primary),
        dict(SiteCode="S2", RefCode="R2", CurrentBatSpecies="Carollia perspicillata",
             CurrentPlantSpecies="Cecropia peltata", Interaction="Frugivory", TrophicGuild=primary),
    ]
    sites = [
        dict(SiteCode="S1", RefCode="R1", Country="Brazil", Precision="Precise", SamplingEffort="NA"),
        dict(SiteCode="S2", RefCode="R2", Country="Mexico", Precision="Not precise", SamplingEffort=""),
    ]
    return {"records": records, "sites": sites, "references": [{"RefCode": "R1"}, {"RefCode": "R2"}]}


class TestNeoBatPreflight(unittest.TestCase):
    def test_binomial(self):
        self.assertTrue(pre.binomial("Ficus insipida"))
        self.assertFalse(pre.binomial("Ficus sp."))
        self.assertFalse(pre.binomial("Unidentified sp.1"))

    def test_network_gate_guild_and_source_quality(self):
        r = pre.audit(fixture())
        self.assertEqual(r["network_candidates_all"], 1)
        self.assertEqual(r["network_candidates_primary"], 1)
        self.assertEqual(r["fruit_site_precision_unknown"], 1)
        self.assertEqual(r["fruit_site_sampling_effort_missing"], 2)
        self.assertIsNone(r["ecological_result"])

    def test_nectarivore_consuming_fruit_not_primary(self):
        r = pre.audit(fixture("Nectarivore"))
        self.assertEqual(r["network_candidates_all"], 1)
        self.assertEqual(r["network_candidates_primary"], 0)

    def test_cross_reference_conflict_reported(self):
        f = fixture()
        f["records"][0]["RefCode"] = "R2"
        self.assertEqual(pre.audit(f)["source_ref_conflict_count"], 1)

    def test_missing_reference_stops(self):
        f = fixture()
        f["records"][0]["RefCode"] = "R3"
        with self.assertRaisesRegex(RuntimeError, "UNJOINED_SOURCE_KEY"):
            pre.audit(f)

    def test_gbif_unresolved_match_not_queried_as_occurrences(self):
        with patch.object(pre, "get", return_value=b'{"rank":"GENUS","matchType":"NONE","confidence":0}'):
            r = pre.gbif_screen([{"bat": "Carollia perspicillata", "primary_candidate": True}])
        self.assertEqual(r["taxon_ambiguous"], 1)
        self.assertEqual(r["search_count_pass"], 0)
        self.assertIsNone(r["ecological_result"])

    def test_gbif_counts_never_assigned_doi_or_spatial_cells(self):
        def fake_get(url):
            if "species/match" in url:
                return b'{"rank":"SPECIES","matchType":"EXACT","confidence":99,"usageKey":1234}'
            return b'{"count":150,"facets":[{"field":"COUNTRY","counts":[{"name":"BR","count":100},{"name":"US","count":50}]}]}'
        with patch.object(pre, "get", side_effect=fake_get):
            r = pre.gbif_screen([{"bat": "Carollia perspicillata", "primary_candidate": True}])
        self.assertEqual(r["records"][0]["regional_records_upper_bound"], 100)
        self.assertFalse(r["records"][0]["spatial_25km_cells_verified"])
        self.assertIsNone(r["GBIF_download_DOI"])
        self.assertEqual(r["search_count_pass"], 1)


if __name__ == "__main__":
    unittest.main()
