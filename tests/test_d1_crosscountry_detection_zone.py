"""Pure synthetic tests only. No external study EDD rows are opened."""
from __future__ import annotations

import csv
from io import StringIO
import math
import unittest

from scripts import d1_crosscountry_detection_zone as d


HEADER = ["ID", "ref", "Country", "full.r", "ndet", "ct_brand",
          "body_mass", "ct_height", "T", "data.order"]


def csv_data(data: list[dict]) -> str:
    obj=StringIO()
    w=csv.DictWriter(obj,fieldnames=HEADER)
    w.writeheader()
    for row in data: w.writerow(row)
    return obj.getvalue()


def example(**kw):
    r = {"ID":"zone1", "ref":"study1", "Country":"A", "full.r":"3.5",
         "ndet":"72", "ct_brand":"Reconyx", "body_mass":"4.0",
         "ct_height":"0.5", "T":"contact", "data.order":"Carnivora"}
    r.update(kw)
    return r


def regions(y_mode="traits"):
    x=[]
    for k in range(6):
        country = "C" + str(k)
        for j in range(12):
            mass=0.5*math.exp(j/5.0)
            z=1.0 + 1.0*math.log(mass)
            if y_mode=="constant":z=2.3
            x.append({"country":country,"brand":"browning" if j%2 else "reconyx",
                      "order":"carnivora" if j%3 else "ungulata", "target":z,
                      "num":(math.log(mass),math.log(.5+(j%4)/3),math.log1p(90+j*10))})
    return x


class TestFrozenD1(unittest.TestCase):
    def test_blob_digest_matches_git_encoding(self):
        assert d.git_blob_sha1(b"test content\n") == "d670460b4b4aece5915caf5c68d12f560a9fe3e4"  # regression hash checked below

    def test_source_gate_rejects_modified_bytes(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_STOP"):
            d.check_source(b"deliberately not published authors' file")

    def test_required_headers(self):
        with self.assertRaisesRegex(ValueError,"SCHEMA_STOP"):
            d.parse_zones("ID,Country\n1,C\n")

    def test_source_zone_id_duplicated(self):
        with self.assertRaisesRegex(ValueError,"SCHEMA_STOP"):
            d.parse_zones(csv_data([example(),example(**{"full.r":"4"})]))

    def test_source_zone_id_blank(self):
        with self.assertRaisesRegex(ValueError,"SCHEMA_STOP"):
            d.parse_zones(csv_data([example(ID="")]))

    def test_contact_mapping(self):
        self.assertEqual(d._seconds(" Contact "),1500.)
        self.assertEqual(d._seconds("120"),120.)
        self.assertIsNone(d._seconds("0"))
        self.assertIsNone(d._seconds("nan"))
        self.assertIsNone(d._seconds("invalid"))

    def test_only_mammalian_orders_and_minimum_events(self):
        rows=[example(),example(ID="zone2",**{"data.order":"Aves"}),
              example(ID="zone3",ndet="49"),example(ID="zone4",ndet="50")]
        z,q=d.parse_zones(csv_data(rows))
        self.assertEqual(len(z),2)
        self.assertEqual(q["source_rows"],4)
        self.assertEqual(q["excluded_not_fixed_mammal_order"],1)
        self.assertEqual(q["excluded_incomplete_or_low_detection"],1)

    def test_positive_finite_fields(self):
        rows=[example(),example(ID="zero",body_mass="0"),
              example(ID="infty",**{"full.r":"inf"}),
              example(ID="bad_height",ct_height="-0.5")]
        z,q=d.parse_zones(csv_data(rows))
        self.assertEqual(len(z),1)
        self.assertEqual(q["excluded_incomplete_or_low_detection"],3)

    def test_basic_gauss_jordan(self):
        r=d.solve_linear([[2.,0.],[0.,3.]],[4.,9.])
        self.assertEqual(r,[2.,3.])
        with self.assertRaisesRegex(ValueError,"MODEL_STOP"):
            d.solve_linear([[0.,0.],[0.,0.]],[1.,2.])

    def test_brand_smoothed_unseen_fallback(self):
        train=regions()[:15]
        model=d.brand_fit(train)
        base=model[0]
        self.assertAlmostEqual(d.predict_brand(model,{"brand":"not-in-training"}),base)
        self.assertTrue(math.isfinite(d.predict_brand(model,{"brand":"browning"})))

    def test_ridge_returns_finite_predictions(self):
        train=regions()[:45]
        model=d.ridge_fit(train)
        self.assertTrue(math.isfinite(d.predict_ridge(model,regions()[0])))
        r=regions()[0].copy()
        r["brand"]="heldout-only"
        r["order"]="new-order"
        self.assertTrue(math.isfinite(d.predict_ridge(model,r)))

    def test_training_only_encoding(self):
        training=regions()[:36]
        fit=d.ridge_fit(training)
        r=regions()[40].copy()
        r["brand"]="brand_not_seen_in_training"
        r["order"]="new_order"
        # Both unknown factor blocks are all zeros; no outside factor encoder fit.
        vector=d._model_vector(r,fit["scalers"],fit["brands"],fit["orders"])
        self.assertEqual(sum(vector[4:]),0.)

    def test_country_holdout_positive_trait_signal(self):
        res=d.evaluate(regions("traits"),{"synthetic":True},{"synthetic":True})
        self.assertEqual(res["status"],"D1_DESCRIPTIVE_COUNTRY_TRANSFER_POSITIVE")
        self.assertGreater(res["primary"]["pooled_gain_M0_minus_M2"],.05)
        self.assertEqual(res["support"]["scorable_heldout_countries"],6)

    def test_country_holdout_null_outcome_negative(self):
        res=d.evaluate(regions("constant"),{"synthetic":True},{"synthetic":True})
        self.assertEqual(res["status"],"D1_NO_USEFUL_INCREMENTAL_COUNTRY_TRANSFER")
        self.assertFalse(res["primary"]["predeclared_positive_rule_passed"])

    def test_insufficient_country_support_stops(self):
        r=d.evaluate(regions()[:38],{}, {})
        self.assertEqual(r["status"],"INSUFFICIENT_COUNTRY_SUPPORT")
        self.assertNotIn("primary",r)

    def test_unseen_brand_reporting(self):
        train=regions()[:25]
        test=regions()[25:27]
        for r in test:r["brand"]="new brand"
        self.assertEqual(d.score_fold(train,test)["unseen_brand_zones"],2)

    def test_country_identifiers_not_exported(self):
        res=d.evaluate(regions(),{}, {})
        self.assertNotIn('"country":"C0"', __import__("json").dumps(res))
        self.assertTrue(all("country_fold_ordinal" in r for r in res["secondary"]["country_fold_summaries_without_country_names"]))


if __name__=="__main__":
    unittest.main()
