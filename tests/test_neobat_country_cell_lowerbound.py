"""Synthetic-only checks for bounded GBIF preflight: no response data retrieved."""
from __future__ import annotations

import importlib.util
from unittest import TestCase, skipUnless
from unittest.mock import patch
from urllib.error import HTTPError
import io

from scripts import neobat_country_cell_lowerbound as sample

HAS_GEO=importlib.util.find_spec("pyproj") is not None

def fake_metadata():
    bats=[
        {"bat":b,"status":"GBIF_COUNTS_ONLY","match":{"rank":"SPECIES","usageKey":i+1},
         "regional_country_counts":{"BR":550,"MX":300,"CR":150,"PA":40,"PE":10,"US":1200},
         "regional_records_upper_bound":1050,
         "world_records":1300}
        for i,b in enumerate(sample.base.BATS)
    ]
    plants=[
        {"plant":p,"status":"GBIF_PLANT_COUNTS_ONLY",
         "match":{"rank":"SPECIES","usageKey":i+100},
         "regional_country_counts":{"BR":100,"MX":95,"CR":30,"PA":20,"PE":10},
         "regional_records_upper_bound":255,
         "world_records":300}
        for i,p in enumerate(sample.base.PLANTS)
    ]
    return {"records":bats},{"plants":plants}

def dummy_country(d,cc,n):
    return {"country":cc,"source_facet_count":n,"status":"SAMPLED_LOWER_BOUND",
            "cell25_lower_bound":6,"cell50_lower_bound":5,
            "cells25_with_reported_uncertainty_le_12500m":5,
            "dataset_keys_in_sample":2,"records_seen":15}

class TestCountryCellLowerBound(TestCase):
    def test_country_rank_max_four_and_stable_ties(self):
        row={"regional_country_counts":{"BR":20,"CR":30,"MX":30,"PA":10,"PE":100,
                                        "US":999,"ZZ":150}}
        self.assertEqual(sample.selected_countries(row),
                         [("PE",100),("CR",30),("MX",30),("BR",20)])

    def test_no_spurious_absence_from_sample_below_gate(self):
        bat,plant=fake_metadata()
        def low(d,cc,n):
            ret=dummy_country(d,cc,n)
            ret["cell25_lower_bound"]=1
            return ret
        r=sample.run(bat,plant,countries_fn=low)
        self.assertEqual(r["status"],"SAMPLED_CELL_LOWER_BOUND_COMPLETE")
        self.assertEqual(r["sufficient_lower_bound_bats"],0)
        self.assertTrue(all(t["status"]=="INDETERMINATE_FROM_BOUNDED_SAMPLE" for t in r["taxa"]))
        self.assertIsNone(r["GBIF_DOWNLOAD_DOI"])

    def test_fixed_taxa_and_pages_denominator(self):
        bat,plant=fake_metadata()
        r=sample.run(bat,plant,countries_fn=dummy_country)
        self.assertEqual(r["target_species_count"],14)
        self.assertEqual(r["country_pages_attempted"],56)
        self.assertEqual(r["country_pages_max"],56)
        self.assertEqual(r["sufficient_lower_bound_bats"],4)
        self.assertEqual(r["sufficient_lower_bound_plants"],10)
        self.assertTrue(r["not_a_census"])
        self.assertIsNone(r["ecological_predictive_effect"])

    def test_rate_limit_circuit_breaker(self):
        bat,plant=fake_metadata()
        def ratelimit(d,cc,n):
            return {"country":cc,"status":"COUNTRY_PAGE_STOP","error":"GBIF_RATE_LIMIT_STOP"}
        r=sample.run(bat,plant,countries_fn=ratelimit)
        self.assertEqual(r["status"],"PARTIAL_SAMPLE_TRANSPORT_STOP")
        self.assertEqual(r["country_pages_attempted"],4)
        self.assertTrue(all(t["status"]=="NOT_QUERIED_API_RATE_LIMIT" for t in r["taxa"][1:]))

    @skipUnless(HAS_GEO,"requires optional pyproj")
    def test_one_country_page_aggregates_only(self):
        raw={"count":400,"results":[
            {"countryCode":"BR","decimalLongitude":-47.5,"decimalLatitude":-15.5,
             "coordinateUncertaintyInMeters":1000,"datasetKey":"d1"},
            {"countryCode":"BR","decimalLongitude":-47.5,"decimalLatitude":-15.5,
             "datasetKey":"d1"},
            {"countryCode":"BR","decimalLongitude":-46.0,"decimalLatitude":-15.0,
             "coordinateUncertaintyInMeters":14000,"datasetKey":"d2"}
        ]}
        with patch.object(sample,"get_page",return_value=raw) as getter:
            r=sample.audit_country({"name":"X","group":"plant","taxonKey":123},"BR",550)
        self.assertEqual(r["status"],"SAMPLED_LOWER_BOUND")
        self.assertEqual(r["cell25_lower_bound"],2)
        self.assertEqual(r["cells25_with_reported_uncertainty_le_12500m"],1)
        self.assertEqual(r["records_seen"],3)
        self.assertFalse(r["fully_enumerated"])
        self.assertNotIn("decimalLongitude",str(r))
        self.assertIn("country",getter.call_args.args[0])
        self.assertEqual(getter.call_args.args[0]["offset"],0)

    def test_429_never_retried(self):
        error=HTTPError("https://api.gbif.org",429,"RateLimited",{},io.BytesIO())
        with patch.object(sample,"urlopen",side_effect=error) as req:
            with self.assertRaisesRegex(RuntimeError,"GBIF_RATE_LIMIT_STOP"):
                sample.get_page({"limit":1})
        self.assertEqual(req.call_count,1)

    def test_pre_flight_facet_gate(self):
        with self.assertRaisesRegex(ValueError,"NO_COUNTRY_FACETS_STOP"):
            sample.selected_countries({"country_count":12})


if __name__=="__main__":
    import unittest
    unittest.main()
